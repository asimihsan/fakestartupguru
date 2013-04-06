from __future__ import division

import os
import sys
import math
import itertools
import operator
import random
import copy
import re
import string
import pprint

from utilities import weighted_choice, strip_leading_spaces_on_punctuation

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "LanguageModel"
LOG_PATH = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, "logs"))
LOG_FILEPATH = os.path.abspath(os.path.join(LOG_PATH, "%s.log" % APP_NAME))
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Logging.
# -----------------------------------------------------------------------------
import logging
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
# -----------------------------------------------------------------------------

class LanguageModel(object):
    """Base class of a general language model. The flow is to:
       - Pass in an interable of ProcessedText objects.
       - Call train().
       - Call get_perplexity() to see how good your model is. This
         value makes more sense when comparing it to the perplexities
         of other language models.
       - Call generate() to create a random sentence that is "likely"
         (not "most likely") in this language model.
    """
    infrequent_word_tokens = [ \
                               #(re.compile("^\d{4}$"),         "__FOUR_DIGIT_NUMERIC__"),
                               #(re.compile("^\d+$"),           "__NUMERIC__"),
                               #(re.compile("^[A-Z]+$"),        "__ALL_CAPITAL__"),
                               #(re.compile("^[A-Z].*$"),       "__FIRST_CAPITAL__"),
                               #(re.compile("^.*[A-Z]$"),       "__LAST_CAPITAL__"),
                               (None,                          "__RARE__"),
                             ]
    infrequent_count_threshold = 1
    start_symbol = "__START__"
    stop_symbol = "__STOP__"
    sentinels = set([start_symbol, stop_symbol])

    def __init__(self, processed_texts, settings):
        self.processed_texts = processed_texts
        self.settings = settings

    def train(self):
        raise NotImplementedError("should have implemented this")

    def generate(self):
        raise NotImplementedError("should have implemented this")

    def _check_invariants(self):
        assert(self.processed_texts is not None)
        assert(self.settings is not None)

    def convert_tokens_to_rare_tokens(self, tokens):
        rare_tokens = []
        for word in tokens:
            if word in self.sentinels:
                rare_tokens.append(word)
                continue
            for (re_obj, output_token) in self.infrequent_word_tokens:
                if re_obj is None or re_obj.match(word):
                    rare_tokens.append(output_token)
                    break
        rare_tokens = tuple(rare_tokens)
        return rare_tokens

    def convert_tokens_to_basic_rare_tokens(self, tokens):
        rare_token = self.infrequent_word_tokens[-1][-1]
        rare_tokens = []
        for token in tokens:
            if token in self.sentinels:
                rare_tokens.append(token)
            else:
                rare_tokens.append(rare_token)
        rare_tokens = [rare_token] * len(tokens)
        return tuple(rare_tokens)

class HMMTrigramMaximumLikelihoodModel(LanguageModel):
    """A Hidden Markov Model that transmits part-of-speech (POS) tags using trigram
    maximum likelihood probabilities, and then with each POS tag emitting a word
    according to bigram maximum likelihood probabilities.

    This is the same model as the POS tagger used in week 2 of the NLP
    Coursera course.

    !!AI yea this whole file is atrocious. One day refactor nicely.
    """

    ngram_count = 3

    def _check_invariants(self):
        pass

    def train(self):
        # ---------------------------------------------------------------------
        #   For q_ML maximum likelihood language models no parameters to
        #   cross validate, so split up input into training and testing.
        # ---------------------------------------------------------------------
        size = len(self.processed_texts)
        testing_size = int(size * self.settings.generator_non_kfold_testing_proportion)
        training_size = (size - testing_size)
        logger.debug("training_size: %s, testing_size: %s" % (training_size, testing_size))

        training_set = self.processed_texts[:training_size]
        testing_set = self.processed_texts[training_size:]
        self.start_symbol = training_set[0].START_SYMBOL
        self.stop_symbol = training_set[0].STOP_SYMBOL
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Calculate counts over the training set.
        #
        #   Store counts in one giant dictionary indexed by a tuple.
        #   -   Unigram counts (e.g. Count('DT')) is keyed by a 1-tuple
        #   -   Bigram counts (e.g. Count('DT', 'NN') is keyed by a 2-tuple.
        #   -   etc.
        #
        #   For the unigram count we need a count of all words. This is keyed
        #   by None.
        #
        #   We'll also need a vocabulary to use for later geneartion.
        # ---------------------------------------------------------------------
        logger.debug("calculating counts...")
        self.vocabulary = set()
        self.counts = {}
        for training_text in training_set:
            # Get a word count using the unigram counts.
            unigram_tags = training_text.ngram_tags[1]
            tag_count = sum(v for (k, v) in unigram_tags.iteritems() if k != self.start_symbol)
            self.counts[None] = self.counts.get(None, 0) + tag_count
            self.vocabulary.update(elem for elem in unigram_tags if elem != self.start_symbol)

            # Get counts for the actual tags.
            for i in xrange(1, self.ngram_count + 1):
                ngram_tags = training_text.ngram_tags[i]
                for (phrase, count) in ngram_tags.iteritems():
                    self.counts[phrase] = self.counts.get(phrase, 0) + count

            # Start of sentence indicators are:
            # - for unigram, Count(('__START__', )) = number of sentences.
            # - for bigram, Count(('__START__', '__START__')) = number of sentences.
            # etc.
            number_of_sentences = len(training_text.tagged_sentences)
            for i in xrange(1, self.ngram_count + 1):
                start_key = tuple([self.start_symbol] * i)
                self.counts[start_key] = self.counts.get(start_key, 0) + number_of_sentences

        # ---------------------------------------------------------------------
        #   Gather the emission bigram counts.
        # ---------------------------------------------------------------------
        self.emissions = {}
        for training_text in training_set:
            for (tag, words_and_counts) in training_text.tags_words_counts.iteritems():
                for (word, count) in words_and_counts.iteritems():
                    key = (tag, word)
                    self.emissions[key] = self.emissions.get(key, 0) + count

        # ---------------------------------------------------------------------
        #   Out-of-vocabulary words are a big problem when evaluating
        #   perplexity; at the same time we don't want to remove all
        #   out-of-vocabulary words or else our subsequent generation will
        #   be boring.
        #
        #   Hence go through all tokens and replace infrequent tokens with
        #   an appropriate rare token from self.infrequent_word_tokens
        #   for the purposes of training.
        #
        #   !!AI I think this is the cause of very low perplexities for
        #   2-gram and up maximum likelihood models. Often there are less
        #   instances of the denomenator than the numerator, because I think
        #   you need to convert words to rare tokens, not whole ngrams.
        # ---------------------------------------------------------------------
        logger.debug("fixing up rare tokens in training set...")
        self.rare_counts = copy.copy(self.counts)
        for (phrase, count) in self.counts.iteritems():
            if count <= self.infrequent_count_threshold:
                del self.rare_counts[phrase]
                rare_key = self.convert_tokens_to_rare_tokens(phrase)
                self.rare_counts[rare_key] = self.rare_counts.get(rare_key, 0) + count

        # Convert all the counts to a log count; we don't need raw counts
        # any more.
        for (k, v) in self.rare_counts.iteritems():
            self.rare_counts[k] = math.log(v, 2)
        for (k, v) in self.counts.iteritems():
            self.counts[k] = math.log(v, 2)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Calculate the perplexity of the language model over the testing
        #   set.
        #
        #   !!AI yea no time!
        # ---------------------------------------------------------------------
        logger.debug("calculating perplexity...")
        # ---------------------------------------------------------------------

    def transmission_tags(self, chunk, counts):
        logger = logging.getLogger("%s.transmission_tags" % APP_NAME)

        # ---------------------------------------------------------------------
        #   Determine the q_ML numerator.
        # ---------------------------------------------------------------------
        numerator = None
        numerator_keys = [chunk,
                          self.convert_tokens_to_rare_tokens(chunk)]
                          #self.convert_tokens_to_basic_rare_tokens(chunk)]
        for numerator_key in numerator_keys:
            if numerator_key in counts:
                numerator = counts[numerator_key]
                break
        if numerator is None:
            logger.error("no numerator found for chunk: '%s'" % (chunk, ))
        assert(numerator is not None)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Determine the q_ML denomenator.
        # ---------------------------------------------------------------------
        denomenator = None
        if len(chunk) == 1:
            denomenator_keys = [None]
        else:
            denomenator_keys = [numerator_key[:-1],
                                self.convert_tokens_to_rare_tokens(numerator_key[:-1])]
                                #self.convert_tokens_to_basic_rare_tokens(chunk[:-1])]
        for denomenator_key in denomenator_keys:
            if denomenator_key in counts:
                denomenator = counts[denomenator_key]
                break
        if denomenator is None:
            logger.error("no denomenator found for chunk: '%s', numerator_key: '%s'" % (chunk, numerator_key))
        assert(denomenator is not None)
        # ---------------------------------------------------------------------

        return numerator - denomenator

    def emission_tags_to_words(self):
        pass

    def generate(self):
        logger = logging.getLogger("%s.NGramMaximumLikelihoodLanguageModel.generate" % APP_NAME)
        logger.debug("entry.")

        # ---------------------------------------------------------------------
        #   First, "transmit" a series of tags using trigram counts.
        #
        #   !!AI almost a total copy-paste of other code, what a waste.
        # ---------------------------------------------------------------------
        sentence_of_tags = [self.start_symbol] * (self.ngram_count - 1)
        while True:
            #logger.debug("top of loop, sentence so far: %s" % (sentence, ))
            if len(sentence_of_tags) != 0 and sentence_of_tags[-1] == self.stop_symbol:
                break
            if self.ngram_count == 1:
                chunk_contents = (tag for tag in self.vocabulary)
            else:
                chunk_contents = (tuple(sentence_of_tags[-(self.ngram_count - 1):] + list(tag))
                                  for tag in self.vocabulary)
            valid_chunk_contents = [chunk for chunk in chunk_contents
                                    if chunk in self.counts
                                    and not all(elem == self.start_symbol for elem in chunk)]
            chunk_contents_and_probabilities = [(chunk, math.pow(2, self.transmission_tags(chunk, self.counts)))
                                                for chunk in valid_chunk_contents]
            next_chunk = weighted_choice(chunk_contents_and_probabilities)
            next_tag = next_chunk[-1]
            sentence_of_tags.append(next_tag)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Then, "emit" a word per tag using bigram counts.
        #
        #   !!AI clearly could use trigram emissions instead of bigram
        #   emissions. Another day perhaps!
        # ---------------------------------------------------------------------
        sentence = []
        for current_tag in sentence_of_tags:
            if current_tag in self.sentinels:
                continue
            emissions = [ (word, count)
                          for ((tag, word), count) in self.emissions.iteritems()
                          if current_tag == tag ]
            emitted_word = weighted_choice(emissions)
            sentence.append(emitted_word)
        # ---------------------------------------------------------------------

        joined_sentence = ' '.join(word for word in sentence)
        return strip_leading_spaces_on_punctuation(joined_sentence)

class NGramMaximumLikelihoodLanguageModel(LanguageModel):
    """Maximum Likelihood language models use one particular n-gram size with
    no backing off, linear interpolation, or bucketing. Hence there are no
    pameters to cross-validate.

    Where theory talks about a 'q' function we call it 'transmissions'.
    Moveover note that in this model we just care about words; part-of-speech
    tags are not used.

    Also if this is a unigram model (self.ngrams == 1) then ignore the
    start symbol, but do not ignore the stop symbol (or else sentences
    would never end!).
    """

    def _check_invariants(self):
        assert(hasattr(self, "ngram_count"))
        super(NGramMaximumLikelihoodLanguageModel, self)._check_invariants()

    def train(self):
        self._check_invariants()
        logger = logging.getLogger("%s.NGramMaximumLikelihoodLanguageModel.train" % APP_NAME)
        logger.debug("entry. self.ngram_count: %s" % self.ngram_count)

        # ---------------------------------------------------------------------
        #   Validate assumptions.
        # ---------------------------------------------------------------------
        assert(self.ngram_count >= 1)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   For q_ML maximum likelihood language models no parameters to
        #   cross validate, so split up input into training and testing.
        # ---------------------------------------------------------------------
        size = len(self.processed_texts)
        testing_size = int(size * self.settings.generator_non_kfold_testing_proportion)
        training_size = (size - testing_size)
        logger.debug("training_size: %s, testing_size: %s" % (training_size, testing_size))

        training_set = self.processed_texts[:training_size]
        testing_set = self.processed_texts[training_size:]
        self.start_symbol = training_set[0].START_SYMBOL
        self.stop_symbol = training_set[0].STOP_SYMBOL
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Calculate counts over the training set.
        #
        #   Store counts in one giant dictionary indexed by a tuple.
        #   -   Unigram counts (e.g. Count('book')) is keyed by a 1-tuple
        #   -   Bigram counts (e.g. Count('the', 'book') is keyed by a 2-tuple.
        #   -   etc.
        #
        #   For the unigram count we need a count of all words. This is keyed
        #   by None.
        #
        #   We'll also need a vocabulary to use for later geneartion.
        # ---------------------------------------------------------------------
        logger.debug("calculating counts...")
        self.vocabulary = set()
        self.counts = {}
        for training_text in training_set:
            # Get a word count using the unigram counts.
            unigram_words = training_text.ngram_words[1]
            word_count = sum(v for (k, v) in unigram_words.iteritems() if k != self.start_symbol)
            self.counts[None] = self.counts.get(None, 0) + word_count
            self.vocabulary.update(elem for elem in unigram_words if elem != self.start_symbol)

            # Get counts for the actual words.
            for i in xrange(1, self.ngram_count + 1):
                ngram_words = training_text.ngram_words[i]
                for (phrase, count) in ngram_words.iteritems():
                    self.counts[phrase] = self.counts.get(phrase, 0) + count

            # Start of sentence indicators are:
            # - for unigram, Count(('__START__', )) = number of sentences.
            # - for bigram, Count(('__START__', '__START__')) = number of sentences.
            # etc.
            number_of_sentences = len(training_text.tagged_sentences)
            for i in xrange(1, self.ngram_count + 1):
                start_key = tuple([self.start_symbol] * i)
                self.counts[start_key] = self.counts.get(start_key, 0) + number_of_sentences

        # ---------------------------------------------------------------------
        #   Out-of-vocabulary words are a big problem when evaluating
        #   perplexity; at the same time we don't want to remove all
        #   out-of-vocabulary words or else our subsequent generation will
        #   be boring.
        #
        #   Hence go through all tokens and replace infrequent tokens with
        #   an appropriate rare token from self.infrequent_word_tokens
        #   for the purposes of training.
        #
        #   !!AI I think this is the cause of very low perplexities for
        #   2-gram and up maximum likelihood models. Often there are less
        #   instances of the denomenator than the numerator, because I think
        #   you need to convert words to rare tokens, not whole ngrams.
        # ---------------------------------------------------------------------
        logger.debug("fixing up rare tokens in training set...")
        self.rare_counts = copy.copy(self.counts)
        for (phrase, count) in self.counts.iteritems():
            if count <= self.infrequent_count_threshold:
                del self.rare_counts[phrase]
                rare_key = self.convert_tokens_to_rare_tokens(phrase)
                self.rare_counts[rare_key] = self.rare_counts.get(rare_key, 0) + count

        # Convert all the counts to a log count; we don't need raw counts
        # any more.
        for (k, v) in self.rare_counts.iteritems():
            self.rare_counts[k] = math.log(v, 2)
        for (k, v) in self.counts.iteritems():
            self.counts[k] = math.log(v, 2)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Calculate the perplexity of the language model over the testing
        #   set.
        # ---------------------------------------------------------------------
        logger.debug("calculating perplexity...")
        # This will be the sum of all log2 probabilities of all sentences in
        # the testing set under this language model.
        testing_probability = 0

        # Need M, total number of words in testing set, to normalize the
        # probabilities.
        # See 'Evaluating Language Models: Perplexity' in NLP notes.
        M = 0
        for testing_text in testing_set:
            unigram_words = testing_text.ngram_words[1]
            word_count = sum(v for v in unigram_words.itervalues())
            M += word_count

            for sentence in testing_text.tagged_sentences:
                words = [word for (word, tag) in sentence]
                padded_words = [testing_text.START_SYMBOL] * (self.ngram_count - 1) + words + [testing_text.STOP_SYMBOL]
                chunked_words = [tuple(padded_words[i:i+self.ngram_count])
                                 for i in xrange(len(padded_words) - (self.ngram_count - 1))]
                transmissions = [self.transmission_words(chunk, self.rare_counts) for chunk in chunked_words]
                testing_probability += sum(transmissions)
        L = testing_probability / M
        self.perplexity = math.pow(2, -L)
        logger.debug("self.perplexity: %s" % self.perplexity)
        # ---------------------------------------------------------------------

    def generate(self):
        logger = logging.getLogger("%s.NGramMaximumLikelihoodLanguageModel.generate" % APP_NAME)
        logger.debug("entry.")

        sentence = [self.start_symbol] * (self.ngram_count - 1)
        while True:
            #logger.debug("top of loop, sentence so far: %s" % (sentence, ))
            if len(sentence) != 0 and sentence[-1] == self.stop_symbol:
                break
            if self.ngram_count == 1:
                chunk_contents = (word for word in self.vocabulary)
            else:
                chunk_contents = (tuple(sentence[-(self.ngram_count - 1):] + list(word))
                                  for word in self.vocabulary)
            valid_chunk_contents = [chunk for chunk in chunk_contents
                                    if chunk in self.counts
                                    and not all(elem == self.start_symbol for elem in chunk)]
            chunk_contents_and_probabilities = [(chunk, math.pow(2, self.transmission_words(chunk, self.counts)))
                                                for chunk in valid_chunk_contents]
            next_chunk = weighted_choice(chunk_contents_and_probabilities)
            next_word = next_chunk[-1]
            sentence.append(next_word)

        joined_sentence = ' '.join([word for word in sentence if word not in self.sentinels])
        return strip_leading_spaces_on_punctuation(joined_sentence)

    def transmission_words(self, chunk, counts):
        logger = logging.getLogger("%s.transmission_words" % APP_NAME)

        # ---------------------------------------------------------------------
        #   Determine the q_ML numerator.
        # ---------------------------------------------------------------------
        numerator = None
        numerator_keys = [chunk,
                          self.convert_tokens_to_rare_tokens(chunk)]
                          #self.convert_tokens_to_basic_rare_tokens(chunk)]
        for numerator_key in numerator_keys:
            if numerator_key in counts:
                numerator = counts[numerator_key]
                break
        if numerator is None:
            logger.error("no numerator found for chunk: '%s'" % (chunk, ))
        assert(numerator is not None)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Determine the q_ML denomenator.
        # ---------------------------------------------------------------------
        denomenator = None
        if len(chunk) == 1:
            denomenator_keys = [None]
        else:
            denomenator_keys = [numerator_key[:-1],
                                self.convert_tokens_to_rare_tokens(numerator_key[:-1])]
                                #self.convert_tokens_to_basic_rare_tokens(chunk[:-1])]
        for denomenator_key in denomenator_keys:
            if denomenator_key in counts:
                denomenator = counts[denomenator_key]
                break
        if denomenator is None:
            logger.error("no denomenator found for chunk: '%s', numerator_key: '%s'" % (chunk, numerator_key))
        assert(denomenator is not None)
        # ---------------------------------------------------------------------

        #if self.ngram_count == 2:
        #    import ipdb; ipdb.set_trace()
        #    pass

        return numerator - denomenator

class UnigramMaximumLikelihoodLanguageModel(NGramMaximumLikelihoodLanguageModel):
    ngram_count = 1

class BigramMaximumLikelihoodLanguageModel(NGramMaximumLikelihoodLanguageModel):
    ngram_count = 2

class TrigramMaximumLikelihoodLanguageModel(NGramMaximumLikelihoodLanguageModel):
    ngram_count = 3

class QuadgramMaximumLikelihoodLanguageModel(NGramMaximumLikelihoodLanguageModel):
    ngram_count = 4



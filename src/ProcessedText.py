import os
import sys
import nltk
import json
import types
import math
import re
import pprint
import string

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "ProcessedText"
LOG_PATH = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, "logs"))
LOG_FILEPATH = os.path.abspath(os.path.join(LOG_PATH, "%s.log" % APP_NAME))
re_unwanted_text = re.compile(r'(?:http://\S+|www.\S+)')
re_unwanted_characters = re.compile("[^%s]" % "".join([elem for elem in string.ascii_letters + string.digits + string.punctuation + string.whitespace]))
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

def process_text(text):
    logger = logging.getLogger("%s.process_text" % APP_NAME)
    logger.debug("entry. text: '%s'" % text)

    # 1. Pre-process raw text to completely remove some things, like
    # URLs.
    text = re_unwanted_text.sub('', text)
    text = re_unwanted_characters.sub('', text)

    # 2. Segment raw text into sentences.
    sentences = nltk.sent_tokenize(text)

    # 3. Tokenize each sentence into words.
    sentences = [nltk.word_tokenize(sent) for sent in sentences]

    # 4. Apply part-of-speech (POS) tags to each word.
    sentences = [nltk.pos_tag(sent) for sent in sentences]

    # 5. Chunk NNPs into tagged groups, e.g. "PERSON", "ORGANIZATION", etc.
    sentences = [nltk.ne_chunk(sent) for sent in sentences]

    logger.debug("sentences:%s" % (pprint.pformat(sentences), ))

    return sentences

class ProcessedTextJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, ProcessedText):
            return super(ProcessedTextJSONEncoder, self).default(obj)
        else:
            return obj.get_dict_representation()

class ProcessedTextJSONDecoder(json.JSONDecoder):
    @staticmethod
    def decode(obj):
        if isinstance(obj, str):
            list_of_dicts = json.loads(obj)
            return [ProcessedTextJSONDecoder.decode(elem) for elem in list_of_dicts]
        else:
            assert(isinstance(obj, dict))
            return ProcessedText.initialize_from_dict(obj)

class ProcessedText(object):
    """Wrapper around an Official ORM object. It will grab the biography and
    store some intermediate objects in itself that will help in subsequent
    language model building."""

    # -------------------------------------------------------------------------
    #   Constants for determining whether the language is English, and
    #   whether the text is interesting.
    #
    #   !!AI surely constants belong in settings.yaml.
    # -------------------------------------------------------------------------
    english_vocab = set(w.lower() for w in nltk.corpus.words.words())
    unusual_proportion_threshold = 0.5
    interesting_words_threshold = 20
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Start and stop symbols.
    # -------------------------------------------------------------------------
    START_SYMBOL = "__START__"
    STOP_SYMBOL = "__STOP__"
    # -------------------------------------------------------------------------

    # 1 is unigram, 2 is bigram, 3 is trigram, ...
    maximum_ngram_size = 4

    @staticmethod
    def calculate_is_text_english(text):
        logger = logging.getLogger("%s.ProcessedText.calculate_is_text_english" % APP_NAME)
        logger.debug("entry. text: %s" % text)
        words = nltk.word_tokenize(text)
        text_vocab = set(w.lower() for w in words if w.lower().isalpha())
        if len(text_vocab) == 0:
            # Can't do much here if there are no words!
            return_value = False
        else:
            unusual_words = text_vocab.difference(ProcessedText.english_vocab)
            unusual_proportion = float(len(unusual_words)) / float(len(text_vocab))
            logger.debug("unusual proportion: '%s'" % (unusual_proportion, ))
            if unusual_proportion  >= ProcessedText.unusual_proportion_threshold:
                return_value = False
            else:
                return_value = True
        logger.debug("returning: %s" % return_value)
        return return_value

    @staticmethod
    def calculate_is_interesting(text):
        words = nltk.word_tokenize(text)
        if len(words) <= ProcessedText.interesting_words_threshold:
            return False
        return True

    # -------------------------------------------------------------------------
    #   Pair of methods to help serialize into deserialize out of JSON.
    # -------------------------------------------------------------------------
    @staticmethod
    def initialize_from_dict(obj):
        pt = ProcessedText(obj['id'], obj['text'], initialize=False)
        pt.is_text_english = obj.get('is_text_english', False)
        pt.is_interesting = obj.get('is_interesting', False)
        pt.tags_words_counts = obj.get('tags_words_counts', None)
        pt.tagged_sentences = obj.get('tagged_sentences', None)

        # ---------------------------------------------------------------------
        #   Convert the lists of (key, value) on the second level back into
        #   dictionaries with tuples as keys.
        # ---------------------------------------------------------------------
        pt.ngram_words = obj.get('ngram_words', None)
        if pt.ngram_words is not None:
            pt.ngram_words = dict( (int(k), dict((tuple(v0), int(v1))
                                   for (v0, v1) in v))
                                   for (k, v) in pt.ngram_words )
        pt.ngram_tags = obj.get('ngram_tags', None)
        if pt.ngram_tags is not None:
            pt.ngram_tags = dict( (int(k), dict((tuple(v0), int(v1))
                                  for (v0, v1) in v))
                                  for (k, v) in pt.ngram_tags )
        # ---------------------------------------------------------------------

        return pt

    def get_dict_representation(self):
        return_value = {}
        return_value['id'] = self.id
        return_value['text'] = self.text
        return_value['is_text_english'] = getattr(self, "is_text_english", False)
        return_value['is_interesting'] = getattr(self, "is_interesting", False)
        if self.is_text_english == False or self.is_interesting == False:
            return return_value

        return_value['tags_words_counts'] = self.tags_words_counts
        return_value['tagged_sentences'] = self.tagged_sentences

        # ---------------------------------------------------------------------
        # JSON only supports using strings as keys of dictionaries. Hence we
        # convert our dictionaries into a sorted list of (key, value) pairs,
        # and convert back to a dict when we deserialize.
        # ---------------------------------------------------------------------
        return_value['ngram_words'] = sorted((k, sorted(v.iteritems()))
                                             for (k, v) in self.ngram_words.iteritems())
        return_value['ngram_tags'] = sorted((k, sorted(v.iteritems()))
                                            for (k, v) in self.ngram_tags.iteritems())
        # ---------------------------------------------------------------------

        return return_value
    # -------------------------------------------------------------------------

    def __init__(self, id, text, initialize=True):
        # ---------------------------------------------------------------------
        #   Store Official ORM index and the raw text.
        # ---------------------------------------------------------------------
        self.id = id
        self.text = text
        # ---------------------------------------------------------------------

        if initialize == True:
            self.initialize()

    def initialize(self):
        # ---------------------------------------------------------------------
        #   Determine if the text is not English, or not interesting. If so
        #   skip the processing below and set some flags to make filtering
        #   easier.
        # ---------------------------------------------------------------------
        if self.calculate_is_text_english(self.text) == False:
            logger.debug("official '%s' does not have English bio_text" % self.id)
            self.is_text_english = False
            return
        self.is_text_english = True
        if self.calculate_is_interesting(self.text) == False:
            logger.debug("official '%s' does not have interesting bio_text" % self.id)
            self.is_interesting = False
            return
        self.is_interesting = True
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Store the tagged and chunked sentences.
        # ---------------------------------------------------------------------
        self.processed_text = process_text(self.text)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Store a bunch of intermediate information to make subsequent
        #   model building and evaluation easier. Here's what's stored:
        #   -   self.ngram_words: a nested dictionary.
        #       -   First level: integer [1,4], for unigram, bigram, etc.
        #       -   Second level key: ngram content, as a tuple. Unigrams are
        #           1-tuples.
        #       -   Second level value: count.
        #   -   self.ngram_tags: a nested dictionary, same format as
        #       self.ngram_words, except for tags. Note that named entities
        #       are tags e.g. "NE-PERSON", "NE-GPE".
        #   -   self.tags_words_counts: a nested dictionary.
        #       -   First level: a tag as a string. e.g. "NNP".
        #       -   Second level key: a word that has been observed to match
        #           this tag.
        #       -   Second level value: count for this (word, tag) pair.
        #   -   self.tagged_sentences: a list of lists. Each sublist
        #       is a tuple (word, tag).
        #   The intention is that:
        #   -   self.ngram_words, by itself, will let you do basic language
        #       models.
        #   -   self.ngram_tags and self.tags_words_counts will let you do
        #       a Hidden Markov Model (n-gram transmission of tags, and
        #       each tag emits a word).
        # ---------------------------------------------------------------------
        self.ngram_words = dict([(i, {}) for i in xrange(1, self.maximum_ngram_size + 1)])
        self.ngram_tags = dict([(i, {}) for i in xrange(1, self.maximum_ngram_size + 1)])
        self.tags_words_counts = {}
        self.tagged_sentences = []
        for sentence_tree in self.processed_text:
            words = []
            tags = []
            tagged_sentence = []
            for element in sentence_tree:
                if type(element) == nltk.tree.Tree:
                    # This is a tree, and hence a chunked named entity. Note
                    # that named entities are always POS tagged as "NNP", so
                    # we don't need them. We treat named entities as a type of
                    # tag.
                    #
                    # Note that for a chunked named entity e.g.
                    #   NE-ORGANIZATION = "Harvard University"
                    #
                    # we convert it to n tags, one per word in the chunk, eg:
                    #
                    #   NE-ORGANIZATION-START = "Harvard"
                    #   NE-ORGANIZATION-CONTINUE = "University"
                    named_entity_type_start = "NE-%s-START" % element.node
                    named_entity_type_continue = "NE-%s-CONTINUE" % element.node
                    contents = [elem[0] for elem in element.leaves()]
                    named_entity_content = [(contents[0], named_entity_type_start)] + \
                                           [(elem, named_entity_type_continue) for elem in contents[1:]]

                    for (word, tag) in named_entity_content:
                        if tag not in self.tags_words_counts:
                            self.tags_words_counts[tag] = {}
                        self.tags_words_counts[tag][word] = self.tags_words_counts[tag].get(word, 0) + 1

                    tags.extend([tag for (word, tag) in named_entity_content])
                    words.extend([word for (word, tag) in named_entity_content])
                    tagged_sentence.extend(named_entity_content)
                else:
                    # This is a (word, tag) pair.
                    word = element[0]
                    words.append(word)
                    tag = element[1]
                    tags.append(tag)
                    tagged_sentence.append((word, tag))
                    if tag not in self.tags_words_counts:
                        self.tags_words_counts[tag] = {}
                    self.tags_words_counts[tag][word] = self.tags_words_counts[tag].get(word, 0) + 1

            self.tagged_sentences.append(tagged_sentence)

            # -----------------------------------------------------------------
            #   Update n-gram counts for both words and tags. Note that
            #   named entities have been added as "NE-*" tags.
            # -----------------------------------------------------------------
            for i in xrange(1, self.maximum_ngram_size + 1):
                number_of_start_symbols = max(i-1, 1)
                padded_words = [self.START_SYMBOL] * number_of_start_symbols + words + [self.STOP_SYMBOL]
                padded_word_ngrams = nltk.ngrams(padded_words, i)
                for ngram in padded_word_ngrams:
                    self.ngram_words[i][ngram] = self.ngram_words[i].get(ngram, 0) + 1

                padded_tags = [self.START_SYMBOL] * number_of_start_symbols + tags + [self.STOP_SYMBOL]
                padded_tag_ngrams = nltk.ngrams(padded_tags, i)
                for ngram in padded_tag_ngrams:
                    self.ngram_tags[i][ngram] = self.ngram_tags[i].get(ngram, 0) + 1
            # -----------------------------------------------------------------

        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   log10 all the counts.
        #   !!AI useless because we need to sum up counts later.
        # ---------------------------------------------------------------------
        #for collection in [self.ngram_words,
        #                   self.ngram_tags,
        #                   self.tags_words_counts]:
        #    for v1 in collection.itervalues():
        #        for (k2, v2) in v1.iteritems():
        #            v1[k2] = math.log10(v2)
        # ---------------------------------------------------------------------


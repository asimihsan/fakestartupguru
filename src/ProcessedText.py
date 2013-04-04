import os
import sys
import nltk

def process_text(text):
    logger = logging.getLogger("%s.process_text" % APP_NAME)
    logger.debug("entry. text: '%s'" % text)

    # 1. Segment raw text into sentences.
    sentences = nltk.sent_tokenize(text)

    # 2. Tokenize each sentence into words.
    sentences = [nltk.word_tokenize(sent) for sent in sentences]

    # 3. Apply part-of-speech (POS) tags to each word.
    sentences = [nltk.pos_tag(sent) for sent in sentences]

    # 4. Chunk NNPs into tagged groups, e.g. "PERSON", "ORGANIZATION", etc.
    sentences = [nltk.ne_chunk(sent) for sent in sentences]

    return sentences

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
    unusual_proportion_threshold = 0.75
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
    def is_text_english(text):
        words = nltk.word_tokenize(text)
        text_vocab = set(w.lower() for w in words if w.lower().isalpha())
        if len(text_vocab) == 0:
            # Can't do much here if there are no words!
            return False
        unusual_words = text_vocab.difference(ProcessedText.english_vocab)
        if float(len(unusual_words)) / float(len(text_vocab)) >= ProcessedText.unusual_proportion_threshold:
            return False
        return True

    @staticmethod
    def is_interesting(text):
        words = nltk.word_tokenize(text)
        if len(words) <= ProcessedText.interesting_words_threshold:
            return False
        return True

    def __init__(self, official):
        # ---------------------------------------------------------------------
        #   Store Official ORM index and the raw text.
        # ---------------------------------------------------------------------
        self.id = official.id
        self.text = official.bio_text
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Determine if the text is not English, or not interesting. If so
        #   skip the processing below and set some flags to make filtering
        #   easier.
        # ---------------------------------------------------------------------
        if self.is_text_english(self.text) == False:
            logger.debug("official '%s' does not have English bio_text" % official)
            self.is_text_english = False
            return
        self.is_text_english = True
        if self.is_interesting(self.text) == False:
            logger.debug("official '%s' does not have interesting bio_text" % official)
            self.is_interesting = False
            return
        self.is_interesting = True
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Store the tagged and chunked sentences.
        #
        #   !!AI given all the counts below may not need to pickle this;
        #   in fact if you don't pickle it this might work with PyPy.
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
        #
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
        for sentence_tree in self.processed_text:
            words = []
            tags = []
            for element in sentence_tree:
                if type(element) == nltk.tree.Tree:
                    # This is a tree, and hence a chunked named entity. Note
                    # that named entities are always POS tagged as "NNP", so
                    # we don't need them. We treat named entities as a type of
                    # tag.
                    named_entity_type = "NE-%s" % element.node
                    named_entity_content = ' '.join([elem[0] for elem in element.leaves()])
                    if named_entity_type not in self.tags_words_counts:
                        self.tags_words_counts[named_entity_type] = {}
                    self.tags_words_counts[named_entity_type][named_entity_content] = \
                        self.tags_words_counts[named_entity_type].get(named_entity_content, 0) + 1

                    # Treat named entities as one "tag", of type e.g. "NE-PERSON"
                    tags.append(named_entity_type)
                    words.extend([elem[0] for elem in element.leaves()])
                else:
                    # This is a (word, tag) pair.
                    word = element[0]
                    words.append(word)
                    tag = element[1]
                    tags.append(tag)
                    if tag not in self.tags_words_counts:
                        self.tags_words_counts[tag] = {}
                    self.tags_words_counts[tag][word] = self.tags_words_counts[tag].get(word, 0) + 1

            # -----------------------------------------------------------------
            #   Update n-gram counts for both words and tags. Note that
            #   named entities have been added as "NE-*" tags.
            # -----------------------------------------------------------------
            for i in xrange(1, self.maximum_ngram_size + 1):
                padded_words = [self.START_SYMBOL] * (i - 1) + words
                if i > 1:
                    padded_words.append(self.STOP_SYMBOL)
                padded_word_ngrams = nltk.ngrams(padded_words, i)
                for ngram in padded_word_ngrams:
                    self.ngram_words[i][ngram] = self.ngram_words[i].get(ngram, 0) + 1

                padded_tags = [self.START_SYMBOL] * (i - 1) + tags
                if i > 1:
                    padded_tags.append(self.STOP_SYMBOL)
                padded_tag_ngrams = nltk.ngrams(padded_tags, i)
                for ngram in padded_tag_ngrams:
                    self.ngram_tags[i][ngram] = self.ngram_tags[i].get(ngram, 0) + 1
            # -----------------------------------------------------------------

        # ---------------------------------------------------------------------


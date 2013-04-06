from __future__ import division

import os
import sys
import math
import itertools

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

    def __init__(self, processed_texts, settings):
        self.processed_texts = processed_texts
        self.settings = settings

    def train(self):
        raise NotImplementedError("should have implemented this")

    def get_perplexity(self):
        raise NotImplementedError("should have implemented this")

    def generate(self):
        raise NotImplementedError("should have implemented this")

    def _check_invariants(self):
        assert(self.processed_texts is not None)
        assert(self.settings is not None)

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

        size = len(self.processed_texts)
        testing_size = int(size * (self.settings.generator_non_kfold_testing_proportion + self.settings.generator_non_kfold_cross_validation_proportion))
        training_size = (size - testing_size)
        logger.debug("training_size: %s, training_size: %s" % (training_size, testing_size))



    def get_perplexity(self):
        logger = logging.getLogger("%s.NGramMaximumLikelihoodLanguageModel.get_perplexity" % APP_NAME)
        logger.debug("entry.")
        return 5

    def generate(self):
        logger = logging.getLogger("%s.NGramMaximumLikelihoodLanguageModel.generate" % APP_NAME)
        logger.debug("entry.")
        return "hello shirley!!"


class UnigramMaximumLikelihoodLanguageModel(NGramMaximumLikelihoodLanguageModel):
    ngram_count = 1

class LanguageModelParameter(object):
    def __init__(self, label, minimum, maximum, granularity):
        self.label = label
        self.minimum = minimum
        self.maximum = maximum
        self.granularity = granularity


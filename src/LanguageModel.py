from __future__ import division

import os
import sys
import math
import itertools

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

    def __init__(self, processed_texts):
        self.processed_texts = processed_texts

    def train(self):
        raise NotImplementedError("should have implemented this")

    def get_perplexity(self):
        raise NotImplementedError("should have implemented this")

    def generate(self):
        raise NotImplementedError("should have implemented this")


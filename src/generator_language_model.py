#!/usr/bin/env python

import os
import sys
import pprint
import json
import random
import copy
import cPickle as pickle

from settings import Settings
from ProcessedText import ProcessedText, ProcessedTextJSONEncoder, ProcessedTextJSONDecoder
from LanguageModel import UnigramMaximumLikelihoodLanguageModel, \
                          BigramMaximumLikelihoodLanguageModel, \
                          TrigramMaximumLikelihoodLanguageModel, \
                          QuadgramMaximumLikelihoodLanguageModel, \
                          HMMTrigramMaximumLikelihoodModel

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "generator_language_model"
LOG_PATH = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, "logs"))
LOG_FILEPATH = os.path.abspath(os.path.join(LOG_PATH, "%s.log" % APP_NAME))
LANGUAGE_MODELS = [ \
                   #UnigramMaximumLikelihoodLanguageModel,
                   BigramMaximumLikelihoodLanguageModel,
                   TrigramMaximumLikelihoodLanguageModel,
                   #QuadgramMaximumLikelihoodLanguageModel,
                   HMMTrigramMaximumLikelihoodModel,
                  ]
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

def use_language_model(language_model_cls, processed_texts, settings):
    logger = logging.getLogger("%s.use_language_model" % APP_NAME)
    logger.debug("entry. language_model_cls: %s" % language_model_cls)

    lm = language_model_cls(processed_texts, settings)
    lm.train()
    logger.debug("generated sentences:")
    for i in xrange(20):
        logger.debug(lm.generate())

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    settings = Settings()

    # -------------------------------------------------------------------------
    #   If the JSON processed data doesn't exist then you haven't run
    #   the scripts in the correct sequence.
    # -------------------------------------------------------------------------
    if not os.path.isfile(settings.analyzer_tagged_chunked_filepath):
        logger.error("Run 'gather.py' first to get raw data, then 'generate_tagged_chunked.py' to process.")
        sys.exit(1)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Load processed biographies, then grab out the interesting English
    #   ones.
    # -------------------------------------------------------------------------
    if os.path.isfile(settings.analyzer_tagged_chunked_pickle_filepath):
        logger.debug("loading processed data from pickle: '%s'" % settings.analyzer_tagged_chunked_pickle_filepath)
        with open(settings.analyzer_tagged_chunked_pickle_filepath, "rb") as f_in:
            processed_biographies = pickle.load(f_in)
    else:
        logger.debug("loading processed data from JSON: '%s'" % settings.analyzer_tagged_chunked_filepath)
        with open(settings.analyzer_tagged_chunked_filepath, "rb") as f_in:
            processed_biographies = json.load(f_in, cls=ProcessedTextJSONDecoder)
    relevant_biographies = [elem for elem in processed_biographies
                            if getattr(elem, "is_interesting", False) == True and
                               getattr(elem, "is_text_english", False) == True]
    random.shuffle(relevant_biographies)
    # -------------------------------------------------------------------------

    for language_model in LANGUAGE_MODELS:
        use_language_model(language_model, relevant_biographies, settings)

if __name__ == "__main__":
    random.seed(4)
    main()


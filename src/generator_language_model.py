#!/usr/bin/env python

import os
import sys
import pprint
import json

import models
from settings import Settings
from ProcessedText import ProcessedText, ProcessedTextJSONEncoder, ProcessedTextJSONDecoder
from LanguageModel import UnigramMaximumLikelihoodLanguageModel

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "generator_language_model"
LOG_PATH = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, "logs"))
LOG_FILEPATH = os.path.abspath(os.path.join(LOG_PATH, "%s.log" % APP_NAME))
LANGUAGE_MODELS = [ \
                   UnigramMaximumLikelihoodLanguageModel,
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
    logger.debug("perplexity is: %s" % lm.get_perplexity())
    logger.debug("generated sentences:")
    for i in xrange(5):
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
    logger.debug("loading processed data from JDON: '%s'" % settings.analyzer_tagged_chunked_filepath)
    with open(settings.analyzer_tagged_chunked_filepath, "rb") as f_in:
        processed_biographies = json.load(f_in, cls=ProcessedTextJSONDecoder)
    relevant_biographies = [elem for elem in processed_biographies
                            if elem.is_interesting == True and elem.is_text_english]
    # -------------------------------------------------------------------------

    for language_model in LANGUAGE_MODELS:
        use_language_model(language_model, relevant_biographies, settings)

if __name__ == "__main__":
    main()


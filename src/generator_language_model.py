#!/usr/bin/env python

import os
import sys
import cPickle as pickle
import pprint

import models
from settings import Settings
from ProcessedText import ProcessedText

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "generator_language_model"
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

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    settings = Settings()

    # -------------------------------------------------------------------------
    #   If the pickled processed data doesn't exist then you haven't run
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
    logger.debug("loading processed data from pickle: '%s'" % settings.analyzer_tagged_chunked_filepath)
    with open(settings.analyzer_tagged_chunked_filepath, "rb") as f_in:
        processed_biographies = pickle.load(f_in)
    relevant_biographies = [elem for elem in processed_biographies
                            if elem.is_interesting == True and elem.is_text_english]
    # -------------------------------------------------------------------------

    import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    main()


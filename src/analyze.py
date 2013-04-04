#!/usr/bin/env python

import os
import sys
import nltk
import pprint

from settings import Settings
import models

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "analyze"
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

def process_text(text):
    logger = logging.getLogger("%s.process_text" % APP_NAME)
    logger.debug("entry. text: '%s'" % text)

    sentences = nltk.sent_tokenize(text)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    sentences = [nltk.ne_chunk(sent) for sent in sentences]

    return sentences

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    settings = Settings()

    # -------------------------------------------------------------------------
    #   Get all Officials with available biographies.
    #
    #   Use execute().iterator() to iterate without caching models, using
    #   less memory for large result sets (from peewee cookbook).
    # -------------------------------------------------------------------------
    officials = [official for official in models.Official.select().execute().iterator()
                 if official.bio_text is not None and
                    len(official.bio_text) > 0]
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Process all the biographies for all officials.
    # -------------------------------------------------------------------------
    processed_biographies = [process_text(official.bio_text) for official in officials[:10]]
    # -------------------------------------------------------------------------

    import ipdb; ipdb.set_trace()


if __name__ == "__main__":
    main()

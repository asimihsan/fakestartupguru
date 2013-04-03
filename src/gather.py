#!/usr/bin/env python2.7

import os
import sys

import settings
import model

# ----------------------------------------------------------------------------
#   Constants.
# ----------------------------------------------------------------------------
APP_NAME = "gather"
LOG_PATH = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, "logs"))
LOG_FILEPATH = os.path.abspath(os.path.join(LOG_PATH, "%s.log" % APP_NAME))
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#   Logging.
# ----------------------------------------------------------------------------
import logging
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
# ----------------------------------------------------------------------------

if __name__ == "__main__:
    main()

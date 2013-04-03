import os
import sys
import requests
import logging

import models

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "utilities"
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


class HttpFetcher(object):
    def get(self, uri):
        logger = logging.getLogger("%s.HttpFetcher.get" % APP_NAME)
        logger.debug("entry. HTTP GET for URI: '%s'" % uri)

        # -------------------------------------------------------------------------
        #   Check to see if we have a previously cached version of the webpage.
        # -------------------------------------------------------------------------
        existing_webpage = models.Webpage.select() \
                                         .where(models.Webpage.uri == uri)
        if existing_webpage.exists():
            webpage = existing_webpage.get()
            logger.debug("Found previously retrieved copy of URI from: '%s'" % webpage.retrieved_date)
            return webpage
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------
        #   Retrieve and persist the webpage to prevent retrieving it repeatedly.
        # -------------------------------------------------------------------------
        response = requests.get(uri)
        webpage = models.Webpage(contents = response.text,
                                 uri = settings.gatherer_swoop_json_uri,
                                 retrieved_date = datetime.datetime.now())
        webpage.save()
        # -------------------------------------------------------------------------

        return webpage


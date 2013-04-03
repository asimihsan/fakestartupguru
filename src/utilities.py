import os
import sys
import requests
import logging
import datetime

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
    # -------------------------------------------------------------------------
    #   startupweekend.org 403's any unusual User-Agent strings, so let's
    #   set up some generic headers to use on all requests here.
    # -------------------------------------------------------------------------
    GENERIC_HEADERS = {
                       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0"
                      }
    # -------------------------------------------------------------------------

    def get(self, uri, refresh=False):
        logger = logging.getLogger("%s.HttpFetcher.get" % APP_NAME)
        logger.debug("entry. HTTP GET for URI: '%s'" % uri)

        # -------------------------------------------------------------------------
        #   Check to see if we have a previously cached version of the webpage.
        # -------------------------------------------------------------------------
        existing_webpage = models.Webpage.select() \
                                         .where(models.Webpage.uri == uri)
        if not refresh and existing_webpage.exists():
            webpage = existing_webpage.get()
            logger.debug("Found previously retrieved copy of URI from: '%s'" % webpage.retrieved_date)
            return webpage
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------
        #   Retrieve and persist the webpage to prevent retrieving it repeatedly.
        # -------------------------------------------------------------------------
        if refresh and existing_webpage.exists():
            logger.debug("deleting existing cached webpage.")
            existing_webpage.get().delete_instance()
        response = requests.get(uri, headers=self.GENERIC_HEADERS)
        if response.status_code != 200:
            logger.warning("non-200 response code %s, headers: %s" % (response.status_code, response.headers))
        webpage = models.Webpage(contents = response.text,
                                 uri = uri,
                                 retrieved_date = datetime.datetime.now())
        webpage.save()
        # -------------------------------------------------------------------------

        return webpage


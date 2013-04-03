#!/usr/bin/env python

import os
import sys
import datetime
import json
import dateutil.parser

from settings import Settings
import models
from utilities import HttpFetcher

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "gather"
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

def setup_database():
    """ Initialize the database file, maybe drop all tables. """

    # -------------------------------------------------------------------------
    #   Set up the database.
    # -------------------------------------------------------------------------
    # !!AI uncomment me when needed.
    #models.drop_all()
    models.initialize()
    # -------------------------------------------------------------------------

def retrieve_swoop_dataset_as_webpage(settings):
    logger = logging.getLogger("%s.retrieve_swoop_dataset" % APP_NAME)
    logger.debug("entry.")

    # -------------------------------------------------------------------------
    #   Fetch the SWOOP dataset.
    # -------------------------------------------------------------------------
    webpage = HttpFetcher().get(settings.gatherer_swoop_json_uri)
    # -------------------------------------------------------------------------

    return webpage

def add_events(swoop_dataset_webpage):
    logger = logging.getLogger("%s.add_events" % APP_NAME)
    logger.debug("entry.")

    # !!AI REMOVEME
    models.Event.drop_table()
    models.Event.create_table()

    json_object = json.loads(swoop_dataset_webpage.contents)
    for element in json_object:

        # ---------------------------------------------------------------------
        #   Don't re-add known SW events
        # ---------------------------------------------------------------------
        swoop_id = element["id"]
        if models.Event.select().where(models.Event.swoop_id == swoop_id).exists():
            logger.debug("Event with SWOOP id %s already exists." % swoop_id)
            continue
        # ---------------------------------------------------------------------

        event = models.Event(city = element["city"],
                             country = element["country"],
                             swoop_id = element["id"])
        event.start_date = dateutil.parser.parse(element["start_date"])
        event.website = element.get("website", None)
        event.twitter_hashtag = element.get("twitter_hashtag", None)
        event.save()

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    settings = Settings()
    setup_database()

    # -------------------------------------------------------------------------
    #   Retrieve SWOOP JSON, add corresponding Events.
    # -------------------------------------------------------------------------
    swoop_dataset_webpage = retrieve_swoop_dataset_as_webpage(settings)
    add_events(swoop_dataset_webpage)
    # -------------------------------------------------------------------------

    events = [event for event in models.Event.select()]
    import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    main()

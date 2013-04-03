#!/usr/bin/env python

import os
import sys
import datetime
import json
import dateutil.parser
import lxml.html
import itertools

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
    """ Given a Webpage ORM object corresponding to the SWOOP JSON dataset
    add a corresponding number of Event ORM objects for SW events."""

    logger = logging.getLogger("%s.add_events" % APP_NAME)
    logger.debug("entry.")

    json_object = json.loads(swoop_dataset_webpage.contents)
    for element in json_object:
        # ---------------------------------------------------------------------
        #   Don't re-add known SW events
        # ---------------------------------------------------------------------
        swoop_id = int(element["id"])
        if models.Event.select().where(models.Event.swoop_id == swoop_id).exists():
            #logger.debug("Event with SWOOP id %s already exists." % swoop_id)
            continue
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Parse JSON then persist Event.
        # ---------------------------------------------------------------------
        event = models.Event(city = element["city"],
                             country = element["country"],
                             swoop_id = element["id"])
        event.start_date = dateutil.parser.parse(element["start_date"])
        event.website = element.get("website", None)
        event.twitter_hashtag = element.get("twitter_hashtag", None)
        event.save()
        # ---------------------------------------------------------------------

    return True

def add_officials(event):
    """ Given an Event ORM object add a correponding number of Official
    ORM objects if there is any information about judges and mentors
    for this event based on the event.

    Note we may have no judges or mentors listed, or not enough information
    about them to do anything.

    Note that the event may be so old that we have to resort to dipping
    into the Internet Archive to get an old version of the site.
    """
    logger = logging.getLogger("%s.add_officials" % APP_NAME)
    logger.debug("entry. event: %s" % event)

    # -------------------------------------------------------------------------
    #   Validate inputs.
    # -------------------------------------------------------------------------
    if not event.website:
        logger.error("Event with SWOOP ID %s does not have website." % event.swoop_id)
        return False
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Note the use of the "safe_website" field; the SWOOP dataset doesn't use
    #   valid URIs.
    # -------------------------------------------------------------------------
    webpage = HttpFetcher().get(event.safe_website)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Go through each judge and mentor and get their biography and social
    #   media links.
    # -------------------------------------------------------------------------
    doc = lxml.html.fromstring(webpage.contents)
    judges_section = doc.get_element_by_id("judges")
    judges = judges_section.cssselect(".judge")
    mentors_section = doc.get_element_by_id("mentors")
    mentors = mentors_section.cssselect(".mentor")
    for official in itertools.chain(judges, mentors):

        # ---------------------------------------------------------------------
        #   Parse official's information from page.
        # ---------------------------------------------------------------------
        full_name = cssselect_or_none(official, ".info h3").text_content().strip()
        job_title = cssselect_or_none(official, ".info .job-title").text_content().strip()
        biography = cssselect_or_none(official, ".info p").text_content().strip()
        twitter_uri = cssselect_or_none(official, ".twitter")
        if twitter_uri is not None:
            twitter_uri = twitter_uri.attrib["href"]
            twitter_username = twitter_uri.split(r'/')[-1]
        else:
            twitter_username = None
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   Persist Official ORM object.
        # ---------------------------------------------------------------------
        if models.Official.select() \
                          .where(models.Official.full_name == full_name,
                                 models.Official.event == event) \
                          .exists():
            logger.debug("Official '%s' already exists." % full_name)
            continue
        official_obj = models.Official(full_name = full_name,
                                       job_title = job_title,
                                       bio_text = biography,
                                       twitter_username = twitter_username,
                                       event = event)
        official_obj.save()
        # ---------------------------------------------------------------------

    # -------------------------------------------------------------------------

    logger.debug("number of officials: %s" % event.officials.count())
    return True

def cssselect_or_none(element, selector):
    return_value = element.cssselect(selector)
    if len(return_value) == 0:
        return_value = None
    else:
        return_value = return_value[0]
    return return_value

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

    # -------------------------------------------------------------------------
    #   !!AI I expect add_officials to fail a lot, largely because who know
    #   what other Startup Weekend's do with their sites. It'll be an uphill
    #   battle to parse them all perfectly.
    # -------------------------------------------------------------------------
    oldest_event_datetime =  datetime.datetime.now() - datetime.timedelta(weeks = 4.5 * 6)
    newest_event_datetime = datetime.datetime.now() - datetime.timedelta(days = 1)
    events = models.Event.select() \
                         .where(models.Event.start_date >= oldest_event_datetime,
                                models.Event.start_date <= newest_event_datetime)
    # !!AI Known good event for testing.
    #events = models.Event.select() \
    #                     .where(models.Event.swoop_id == 1524)
    for event in events:
        try:
            add_officials(event)
        except:
            logger.exception("Unhandled exception for event with SWOOP id: '%s', URI: '%s'" % (event.swoop_id, event.safe_website))
        logger.debug("total number of officials: %s" % models.Official.select().count())
    # -------------------------------------------------------------------------

    import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    main()

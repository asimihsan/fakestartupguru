import os
import sys
from peewee import SqliteDatabase, Model, CharField, DateTimeField, \
                   ForeignKeyField, IntegerField, DoubleField, TextField
# ----------------------------------------------------------------------------
#   Constants.
# ----------------------------------------------------------------------------
APP_NAME = "models"
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#   Logging.
# ----------------------------------------------------------------------------
import logging
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#   Load Settings
# ----------------------------------------------------------------------------
from settings import Settings
settings = Settings()
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#   Peewee ORM models.
# ----------------------------------------------------------------------------
db = SqliteDatabase(settings.gatherer_sqlite_filepath)

class BaseDatabaseModel(Model):
    class Meta:
        database = db

class Webpage(BaseDatabaseModel):
    contents = TextField()
    uri = CharField()
    retrieved_date = DateTimeField()

    class Meta:
        indexes = (
            (('uri', ), True),
        )

class Event(BaseDatabaseModel):
    city = CharField()
    state = CharField(null=True)
    country = CharField()
    swoop_id = IntegerField()
    start_date = DateTimeField()
    twitter_hashtag = CharField(null=True)
    website = CharField(null=True)
    latitude = DoubleField(null=True)
    longitude = DoubleField(null=True)

    class Meta:
        indexes = (
            (('swoop_id', ), True),
        )

    def __unicode__(self):
        return "swoop_id: '%s', city: '%s', country: '%s', start_date: '%s', website: '%s'" % \
            (self.swoop_id, self.city, self.country, self.start_date, self.website)

    @property
    def safe_website(self):
        """ SWOOP dataset does not contain valid URIs, so fix them up here."""
        if not self.website.startswith("http://"):
            return "http://%s" % self.website
        return self.website

class Official(BaseDatabaseModel):
    full_name = CharField()
    job_title = CharField(null=True)
    twitter_username = CharField(null=True)
    bio_text = TextField(null=True)
    event = ForeignKeyField(Event, related_name='officials')

    def __unicode__(self):
        return "full_name: %s, job_title: %s, twitter_username: %s, event: %s" % \
            (self.full_name, self.job_title, self.twitter_username, self.event)

models_in_create_order = [
                          Webpage,
                          Event,
                          Official,
                         ]
models_in_delete_order = [
                          Official,
                          Event,
                          Webpage,
                         ]

def create_directory_and_file():
    # -------------------------------------------------------------------------
    #   Create appropriate directories and touch SQLite database file.
    # -------------------------------------------------------------------------
    directory = os.path.dirname(settings.gatherer_sqlite_filepath)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    if not os.path.isfile(settings.gatherer_sqlite_filepath):
        with open(settings.gatherer_sqlite_filepath, "wb") as f_out:
            pass
    # -------------------------------------------------------------------------

def initialize():
    logger = logging.getLogger("%s.initialize" % APP_NAME)
    logger.debug("entry.")

    create_directory_and_file()

    # -------------------------------------------------------------------------
    #   Create tables.
    # -------------------------------------------------------------------------
    for model in models_in_create_order:
        logger.debug("model: %s" % model)
        if not model.table_exists():
            logger.debug("table does not exist.")
            model.create_table()
    # -------------------------------------------------------------------------

def drop_all():
    logger = logging.getLogger("%s.drop_all" % APP_NAME)
    logger.debug("entry.")

    create_directory_and_file()

    # -------------------------------------------------------------------------
    #   Drop tables.
    # -------------------------------------------------------------------------
    for model in models_in_delete_order:
        logger.debug("model: %s" % model)
        if model.table_exists():
            logger.debug("table exists.")
            model.drop_table()
    # -------------------------------------------------------------------------


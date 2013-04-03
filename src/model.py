import os
import sys
from peewee import SqliteDatabase, Model, CharField, DateTimeField,
                   ForeignKeyField, IntegerField, DoubleField

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

class Webpage(Model):
    contents = CharField()
    uri = CharField()
    retrieved_date = DateTimeField()

class Event(BaseDatabaseModel):
    city = CharField()
    state = CharField(null=True)
    country = CharField()
    swoop_id = IntegerField()
    start_date = DateTimeField()
    twitter_hashtag = CharField(null=True)
    website = CharField()
    latitude = DoubleField(null=True)
    longitude = DoubleField(null=True)

class Official(BaseDatabaseModel):
    full_name = CharField()
    twitter_username = CharField(null=True)
    bio_text = CharField(null=True)
    type = IntegerField(

    event = ForeignKeyField(Event, related_name='officials')
# ----------------------------------------------------------------------------

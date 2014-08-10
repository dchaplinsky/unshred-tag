import datetime
from mongoengine import (
    StringField, IntField, SequenceField, Document, DateTimeField, ListField)


class Shreds(Document):
    name = StringField(max_length=20, default='')
    usersCount = IntField(default=0)
    usersSkipped = SequenceField(default=[])
    usersProcessed = SequenceField(default=[])
    summarizedTags = SequenceField(default=[])


class Tags(Document):
    description = StringField(max_length=200, default='')
    title = StringField(max_length=200, default='', primary_key=True)
    usages = IntField(default=0)
    shreds = SequenceField(default=[])
    synonyms = ListField(StringField(max_length=200))


class Batches(Document):
    name = StringField(primary_key=True, max_length=200)
    created = DateTimeField(default=datetime.datetime.now)
    import_took = IntField(default=0)
    pages_processed = IntField(default=0)
    shreds_created = IntField(default=0)

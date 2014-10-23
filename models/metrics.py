import datetime
from mongoengine import (
    FloatField, IntField, DateTimeField, ListField, ReferenceField,
    StringField, CASCADE)
from flask.ext.mongoengine import Document

from .user import User
from .shreds import Shreds


class TaggingSpeed(Document):
    """
    Metric to measure time required to process single shred and see
    how that correlates with UI changes.
    """

    tagged_at = DateTimeField(default=datetime.datetime.utcnow)
    msec = FloatField()
    tags_count = IntField()
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    shred = ReferenceField(Shreds, reverse_delete_rule=CASCADE)


class ShredsDistances(Document):
    """
    Distance types are:
    - jaccard: Jaccard distance. http://en.wikipedia.org/wiki/Jaccard_index
    - tf-idf: term frequency-inverse document frequency http://en.wikipedia.org/wiki/Tf-idf
    """

    shreds_pair = ListField(ReferenceField(Shreds), default=[])
    distance_type = StringField(max_length=10, default='')
    distance = FloatField()

    meta = {
        'indexes': ['shreds_pair', 'distance', 'distance_type'],
        'index_background': True,
    }

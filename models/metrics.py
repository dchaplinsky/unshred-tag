import datetime
from mongoengine import (
    FloatField, IntField, DateTimeField, ReferenceField, CASCADE)
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

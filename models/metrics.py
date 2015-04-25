import datetime
import random

from mongoengine import (
    FloatField, IntField, DateTimeField, ListField, ReferenceField,
    StringField, CASCADE)
from flask.ext.mongoengine import Document

from .user import User
from .shreds import Cluster


class TaggingSpeed(Document):
    """
    Metric to measure time required to process single shred and see
    how that correlates with UI changes.
    """

    tagged_at = DateTimeField(default=datetime.datetime.utcnow)
    msec = FloatField()
    tags_count = IntField()
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    cluster = ReferenceField(Cluster, reverse_delete_rule=CASCADE)


class ShredsDistances(Document):
    """
    Distance types are:
    - jaccard: Jaccard distance. http://en.wikipedia.org/wiki/Jaccard_index
    - tf-idf: term frequency-inverse document frequency
            http://en.wikipedia.org/wiki/Tf-idf
    """

    shreds_pair = ListField(ReferenceField(Cluster))
    distance_type = StringField(max_length=10, choices=('jaccard', ))
    distance = FloatField(min_value=0, max_value=1)

    meta = {
        'indexes': ['shreds_pair', 'distance', 'distance_type'],
        'index_background': True,
    }

    @classmethod
    def get_close_pair(cls):
        total_num_pairs = cls.objects.count()
        # Mean = 1/lambd = total_num_pairs / 10, i.e. 50% chance that returned
        # pair will be within lowest 10% distances.
        lambd = 10. / total_num_pairs
        idx = -1
        while not 0 <= idx <= total_num_pairs:
            idx = int(random.expovariate(lambd))

        return cls.objects.order_by('-distance')[idx]

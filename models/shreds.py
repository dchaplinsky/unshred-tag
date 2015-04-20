import datetime
from collections import Counter
from itertools import chain
import random

from mongoengine import (
    StringField, IntField, DateTimeField, ListField, BooleanField,
    ReferenceField, EmbeddedDocument, EmbeddedDocumentField, FloatField,
    CASCADE, QuerySet)
from flask.ext.mongoengine import Document

from .user import User


class Features(EmbeddedDocument):
    histogram_clean = ListField(IntField())
    height_mm = FloatField(default=0.0)
    histogram_full = ListField(IntField())
    width_mm = FloatField(default=0.0)
    area = IntField(default=0)
    dominant_colours = ListField(StringField())
    solidity = FloatField(default=0.0)
    colour_names = ListField(StringField())
    ratio = FloatField(default=0.0)
    width = IntField(default=0)
    height = IntField(default=0)


class ShredTags(EmbeddedDocument):
    user = ReferenceField(User)
    tags = ListField(StringField())
    recognizable_chars = StringField()
    angle = IntField(default=0)
    pages = ListField(ReferenceField("Pages"))


# Immutable once imported from CV.
class Shred(Document):
    id = StringField(max_length=200, default='', primary_key=True)
    name = IntField()
    features = EmbeddedDocumentField(Features)
    tags = ListField(StringField())
    contour = ListField(ListField(IntField()))
    sheet = StringField()
    piece_fname = StringField()
    piece_in_context_fname = StringField()
    mask_fname = StringField()

    def get_auto_tags(self):
        mapping = Tags.objects.get_tag_synonyms()
        auto = [mapping.get(suggestion)
                for suggestion in self.tags]

        return filter(None, set(auto))

    def __unicode__(self):
        return "Shred: %s" % self.id

class ClusterMember(EmbeddedDocument):
    """Describes shred membership within a cluster.

    Relative shred position is stored as rotation angle (in radians) and
    (x, y) translation relative to cluster origin.
    """
    shred = ReferenceField(Shred)
    position = ListField(FloatField())
    angle = FloatField()

    def __unicode__(self):
        return self.shred.id


class Cluster(Document):
    """Cluster of one or more shreds.

    Shred membership described with a ClusterMember embedded document, which
    contains a reference to the shred and its relative position and angle in a
    cluster.

    Cluster also contains user-generated tagging results (tags field).
    """
    id = StringField(max_length=200, default='', primary_key=True)

    users_count = IntField(default=0, db_field='usersCount')
    users_skipped = ListField(ReferenceField(User), db_field='usersSkipped')
    users_processed = ListField(ReferenceField(User),
                                db_field='usersProcessed')

    batch = StringField()
    tags = ListField(EmbeddedDocumentField(ShredTags))

    members = ListField(EmbeddedDocumentField(ClusterMember))
    parents = ListField(ReferenceField('Cluster'))

    def __unicode__(self):
        return self.id

    @property
    def features(self):
        # TODO: persist features on creation.
        return self.members[0].shred.features

    def get_user_tags(self, user):
        for shred_tags in self.tags:
            # in some rare cases user reference from shred_tags has no pk field
            if shred_tags.user.id == user.pk:
                return shred_tags
        return None

    def get_auto_tags(self):
        return set(sum((member.shred.get_auto_tags()
                        for member in self.members), []))

    @property
    def get_tags(self):
        return sum([st.tags for st in self.tags], [])

    def get_repeated_tags(self, repeats=2):
        tags_counts = Counter(self.get_tags)
        return [tag for tag, count in tags_counts.items() if count >= repeats]

    @staticmethod
    def next_for_user(user, users_per_shred):
        # TODO: add randomisation.
        cluster = Cluster\
            .objects(users_processed__ne=user.id, users_skipped__ne=user.id,
                     users_count__lte=users_per_shred)\
            .order_by("users_count").first()

        if cluster:
            return cluster

        cluster = Cluster\
            .objects(users_skipped=user.id, users_count__lte=users_per_shred)\
            .order_by("users_count").first()

        if cluster:
            Cluster.objects(id=cluster.id).update_one(
                pull__users_skipped=user.id)

        return cluster

    @classmethod
    def get_some(cls, batch=None):
        # TODO: Pick appropriate cluster.
        qs = cls.objects
        if batch is not None:
          qs = qs.filter(batch=batch)
        num = random.randint(0, qs.count()-1)
        some_clusters = qs.skip(num).limit(1)
        if some_clusters:
            return some_clusters[0]
        return None

    @property
    def num_members(self):
        return len(self.members)

class TagsQS(QuerySet):
    def get_base_tags(self, order_by_category=False):
        qs = self.filter(is_base=True)
        if order_by_category:
            return qs.order_by("category", "-usages")

        return qs.order_by("-usages")

    def get_tag_synonyms(self):
        mapping = {}
        for t in self.filter(synonyms__exists=True):
            for s in t["synonyms"]:
                mapping[s] = t["title"]

        return mapping


class Tags(Document):
    title = StringField(max_length=200, default='', primary_key=True)
    description = StringField(max_length=200, default='')
    usages = IntField(default=0)
    shreds = ListField(ReferenceField(Cluster))
    synonyms = ListField(StringField(max_length=200))
    is_base = BooleanField(default=True)
    category = StringField(max_length=200, default='')
    created_by = ReferenceField(User, reverse_delete_rule=CASCADE)
    created_at = DateTimeField(default=datetime.datetime.now)
    hotkey = StringField(max_length=10, default='')

    meta = {'queryset_class': TagsQS}

    def __unicode__(self):
        return self.title


class Pages(Document):
    name = StringField(max_length=200)
    created_by = ReferenceField(User, reverse_delete_rule=CASCADE)
    shreds = ListField(ReferenceField(Cluster))
    created = DateTimeField(default=datetime.datetime.now)

    def __unicode__(self):
        return self.name

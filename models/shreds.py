from collections import Counter
import datetime
import random

import jinja2

from mongoengine import (
    StringField, IntField, DateTimeField, ListField, BooleanField,
    ReferenceField, EmbeddedDocument, EmbeddedDocumentField, FloatField,
    CASCADE, QuerySet)
from flask.ext.mongoengine import Document

from .user import User


class Features(EmbeddedDocument):
    histogram_clean = ListField(IntField())
    height_mm = FloatField(required=True)
    histogram_full = ListField(IntField())
    width_mm = FloatField(required=True)
    area = IntField(required=True)
    dominant_colours = ListField(StringField())
    solidity = FloatField(required=True)
    colour_names = ListField(StringField())
    ratio = FloatField(required=True)
    width = IntField(required=True)
    height = IntField(required=True)


class ShredTags(EmbeddedDocument):
    user = ReferenceField(User)
    tags = ListField(StringField())
    recognizable_chars = StringField()
    angle = IntField(default=0)
    pages = ListField(ReferenceField("Pages"))


# Immutable once imported from CV.
class Shred(Document):
    id = StringField(max_length=200, default='', primary_key=True)
    name = IntField(required=True)
    features = EmbeddedDocumentField(Features)
    tags = ListField(StringField())
    contour = ListField(ListField(IntField()))
    sheet = StringField(required=True)
    piece_fname = StringField(required=True)
    piece_in_context_fname = StringField(required=True)
    mask_fname = StringField(required=True)


    def _feature_tags(self):
        return ['color:%s' % c for c in self.features.dominant_colours]

    @property
    def auto_tags(self):
        mapping = Tags.objects.get_tag_synonyms()
        auto = [mapping.get(suggestion, suggestion)
                for suggestion in self.tags] + self._feature_tags()

        return auto

    def __unicode__(self):
        return "Shred: %s" % self.id

class ClusterMember(EmbeddedDocument):
    """Describes shred membership within a cluster.

    Relative shred position is stored as rotation angle (in radians) and
    (x, y) translation relative to cluster origin.
    """
    shred = ReferenceField(Shred, required=True)
    position = ListField(FloatField())
    angle = FloatField(required=True)

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

    batch = StringField(required=True)
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

    @property
    def auto_tags(self):
        return sum((member.shred.auto_tags for member in self.members), [])

    @property
    def render_auto_tags(self):
        auto_tags = self.auto_tags
        res = []
        for t in auto_tags:
            if not t.startswith('color:'):
                res.append(jinja2.escape(t))
                continue

            color_tmpl = (
                "<span style='height:15px;width:40px;background-color:#%s;display:inline-block'>" +
                "&nbsp;</span>")

            res.append(color_tmpl % t[len('color:'):])

        return jinja2.Markup(', '.join(res))

    @property
    def all_tags(self):
        return sorted(set(t for st in self.tags for t in st.tags))

    def get_repeated_tags(self, repeats=2):
        tags_counts = Counter(self.all_tags)
        return (set(
            [tag for tag, count in tags_counts.items() if count >= repeats]) |
            set(self.auto_tags))

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

    @property
    def image_html(self):
        if self.num_members != 1:
            return ''

        return jinja2.Markup('<img src="%s" />' %
                             self.members[0].shred.piece_fname)



class TagsQS(QuerySet):
    _synonyms_cache = None
    def get_base_tags(self, order_by_category=False):
        qs = self.filter(is_base=True)
        if order_by_category:
            return qs.order_by("category", "-usages")

        return qs.order_by("-usages")

    def get_tag_synonyms(self):
        if self._synonyms_cache is None:
            mapping = {}
            for t in self.filter(synonyms__exists=True):
                for s in t["synonyms"]:
                    mapping[s] = t["title"]
            self.__class__._synonyms_cache = mapping
        return self._synonyms_cache


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

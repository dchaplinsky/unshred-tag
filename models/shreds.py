import datetime
from collections import Counter
from itertools import chain
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
    topmost = ListField(IntField())
    solidity = FloatField(default=0.0)
    colour_names = ListField(StringField())
    ratio = FloatField(default=0.0)
    bottommost = ListField(IntField())
    width = IntField(default=0)
    height = IntField(default=0)


class ShredTags(EmbeddedDocument):
    user = ReferenceField(User)
    tags = ListField(StringField())
    recognizable_chars = StringField()
    angle = IntField(default=0)
    pages = ListField(ReferenceField("Pages"))


class Shreds(Document):
    id = StringField(max_length=200, default='', primary_key=True)
    name = IntField()
    users_count = IntField(default=0, db_field='usersCount')
    users_skipped = ListField(ReferenceField(User), db_field='usersSkipped')
    users_processed = ListField(ReferenceField(User),
                                db_field='usersProcessed')
    features = EmbeddedDocumentField(Features)
    tags_suggestions = ListField(StringField())
    piece_in_context_fname = StringField()
    features_fname = StringField()
    contour = ListField(ListField(ListField(IntField())))
    sheet = StringField()
    piece_fname = StringField()
    batch = ReferenceField('Batches')
    tags = ListField(EmbeddedDocumentField(ShredTags))

    def __unicode__(self):
        return self.id

    def get_user_tags(self, user):
        for shred_tags in self.tags:
            # in some rare cases user reference from shred_tags has no pk field
            if shred_tags.user.id == user.pk:
                return shred_tags
        return None

    def get_tags(self):
        return chain(*[st.tags for st in self.tags])

    def get_repeated_tags(self, repeats=2):
        tags_counts = Counter(self.get_tags())
        return [tag for tag, count in tags_counts.items() if count >= repeats]

    @staticmethod
    def next_for_user(user, users_per_shred):
        shred = Shreds\
            .objects(users_processed__ne=user.id, users_skipped__ne=user.id,
                     users_count__lte=users_per_shred)\
            .order_by("batch", "users_count").first()

        if shred:
            return shred

        shred = Shreds\
            .objects(users_skipped=user.id, users_count__lte=users_per_shred)\
            .order_by("batch", "users_count").first()

        if shred:
            Shreds.objects(id=shred.id).update_one(pull__users_skipped=user.id)

        return shred

    def get_auto_tags(self):
        mapping = Tags.objects.get_tag_synonyms()
        auto = [mapping.get(suggestion)
                for suggestion in self.tags_suggestions]

        return filter(None, set(auto))


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
    shreds = ListField(ReferenceField(Shreds))
    synonyms = ListField(StringField(max_length=200))
    is_base = BooleanField(default=True)
    category = StringField(max_length=200, default='')
    created_by = ReferenceField(User, reverse_delete_rule=CASCADE)
    created_at = DateTimeField(default=datetime.datetime.now)
    hotkey = StringField(max_length=10, default='')

    meta = {'queryset_class': TagsQS}

    def __unicode__(self):
        return self.title


class Batches(Document):
    name = StringField(primary_key=True, max_length=200)
    created = DateTimeField(default=datetime.datetime.now)
    import_took = IntField(default=0)
    pages_processed = IntField(default=0)
    shreds_created = IntField(default=0)

    def __unicode__(self):
        return self.name


class Pages(Document):
    name = StringField(max_length=200)
    created_by = ReferenceField(User, reverse_delete_rule=CASCADE)
    shreds = ListField(ReferenceField(Shreds))
    created = DateTimeField(default=datetime.datetime.now)

    def __unicode__(self):
        return self.name

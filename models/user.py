from mongoengine import BooleanField, DateTimeField, EmailField, IntField, \
        ListField, SequenceField, StringField
from flask.ext.login import UserMixin, AnonymousUserMixin
from flask.ext.mongoengine import Document
import datetime


class User(Document, UserMixin):
    username = StringField(max_length=200)
    password = StringField(max_length=200, default='')
    name = StringField(max_length=100)
    email = EmailField()
    active = BooleanField(default=True)
    admin = BooleanField(default=False)
    last_login = DateTimeField(default=datetime.datetime.now)
    skipped = IntField(default=0)
    processed = IntField(default=0)
    tags = ListField(StringField(), default=[])
    tags_count = IntField(default=0, db_field='tagsCount')

    def is_active(self):
        return self.active

    def is_admin(self):
        return self.admin or False

    def __unicode__(self):
        return self.username


class Anonymous(AnonymousUserMixin):
    name = u"Anonymous"


from mongoengine import StringField, EmailField, BooleanField, Document
from flask.ext.login import UserMixin

class User(Document, UserMixin):
    username = StringField(max_length=200)
    password = StringField(max_length=200, default='')
    name = StringField(max_length=100)
    email = EmailField()
    active = BooleanField(default=True)

    def is_active(self):
        return self.active

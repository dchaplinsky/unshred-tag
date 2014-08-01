from mongoengine import StringField, IntField, SequenceField, ListField, Document

class Shreds(Document):
    pass

class Tags(Document):
    description = StringField(max_length=200, default='')
    title = StringField(max_length=200, default='')


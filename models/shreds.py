from mongoengine import StringField, IntField, SequenceField, ListField, Document

class Shreds(Document):
    name = StringField(max_length=20, default='')
    usersCount = IntField(default=0)
    usersSkipped = SequenceField(default=[])
    usersProcessed = SequenceField(default=[])
    summarizedTags = SequenceField(default=[])


class Tags(Document):
    description = StringField(max_length=200, default='')
    title = StringField(max_length=200, default='')
    usages = IntField(default=0)
    shreds = SequenceField(default=[])


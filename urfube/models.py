from peewee import *

from .database import db


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True)
    # email = CharField()
    password = CharField()


class Video(BaseModel):
    title = CharField()
    description = CharField()
    author = CharField()
    views = IntegerField(default=0)
    user = ForeignKeyField(User, backref='videos')
    created = DateTimeField()


class History(BaseModel):
    video_id = IntegerField()
    timestamp = FloatField()
    length = FloatField()
    user = ForeignKeyField(User, backref='history')


class Comment(BaseModel):
    content = CharField()
    user = ForeignKeyField(User, backref='comments')
    video = ForeignKeyField(Video, backref='comments')
    created = DateTimeField()


class Like(BaseModel):
    user = ForeignKeyField(User, backref='likes')
    video = ForeignKeyField(Video, backref='likes')
    class Meta:
        primary_key = CompositeKey('user', 'video')

class Subscription(BaseModel):
    subscriber = ForeignKeyField(User, backref='subscribers')
    channel = ForeignKeyField(User, backref='subscriptions')

    class Meta:
        primary_key = CompositeKey('subscriber', 'channel')
        indexes = (
            (('subscriber', 'channel'), True),
        )
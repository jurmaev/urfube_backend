from peewee import *

from .database import db


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True)
    email = CharField()
    password = CharField()


class Video(BaseModel):
    title = CharField()
    description = CharField()
    author = CharField()
    views = IntegerField(default=0)
    user = ForeignKeyField(User, backref='videos')


class History(BaseModel):
    video_id = IntegerField()
    timestamp = FloatField()
    length = FloatField()
    # date_visited = DateTimeField()
    user = ForeignKeyField(User, backref='history')


class Comment(BaseModel):
    content = CharField()
    user = ForeignKeyField(User, backref='comments')
    video = ForeignKeyField(Video, backref='comments')


class Like(BaseModel):
    user = ForeignKeyField(User, backref='likes')
    video = ForeignKeyField(Video, backref='likes')

class Subscription(BaseModel):
    subscriber = ForeignKeyField(User, backref='subscribers')
    channel = ForeignKeyField(User, backref='subscriptions')

    class Meta:
        # `indexes` is a tuple of 2-tuples, where the 2-tuples are
        # a tuple of column names to index and a boolean indicating
        # whether the index is unique or not.
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('subscriber', 'channel'), True),
        )
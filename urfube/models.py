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
    user = ForeignKeyField(User, backref='videos')


class History(BaseModel):
    video_id = IntegerField()
    timestamp = IntegerField()
    date_visited = DateTimeField()
    user = ForeignKeyField(User, backref='history')


class Comment(BaseModel):
    content = CharField()
    user = ForeignKeyField(User, backref='comments')
    video = ForeignKeyField(Video, backref='comments')
#
#
# class Like(BaseModel):
#     user = ForeignKeyField(User, backref='likes')
#     video = ForeignKeyField(User, backref='likes')

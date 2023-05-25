import datetime
from typing import Any

import peewee
from pydantic import BaseModel
from pydantic.utils import GetterDict


class PeeweeGetterDict(GetterDict):
    def get(self, key: Any, default: Any = None):
        res = getattr(self._obj, key, default)
        if isinstance(res, peewee.ModelSelect):
            return list(res)
        return res


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserLogin):
    id: int

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class VideoUpload(BaseModel):
    title: str
    description: str


class Video(VideoUpload):
    id: int
    author: str
    user_id: int
    views: int
    created: datetime.datetime

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class History(BaseModel):
    video_id: int
    timestamp: float
    length: int

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class VideoReturn(BaseModel):
    title: str
    created: datetime.datetime
    author: str
    id: int
    timestamp: float
    progress: float
    image_link: str
    profile_link: str
    views: int


class CommentUpload(BaseModel):
    content: str
    video_id: int


class VideoComment(BaseModel):
    content: str
    author: str
    id: int
    created: datetime.datetime
    profile_link: str


class Comment(CommentUpload):
    id: int
    user_id: int
    created: datetime.datetime

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class Like(BaseModel):
    user_id: int
    video_id: int

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class Subscription(BaseModel):
    subscriber: int
    channel: int

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class ChannelInfo(BaseModel):
    channel: str
    subscribers: int
    videos: int
    profile_link: str

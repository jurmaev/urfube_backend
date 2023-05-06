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


class UserCreate(UserLogin):
    email: str


class User(UserCreate):
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

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class VideoReturn(Video):
    image_link: str


class History(BaseModel):
    video_id: int
    timestamp: float
    length: int

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class HistoryReturn(BaseModel):
    title: str
    description: str
    author: str
    video_id: int
    timestamp: float
    progress: float
    image_link: str
    # date_visited: datetime.datetime


class CommentUpload(BaseModel):
    content: str
    video_id: int


class VideoComment(BaseModel):
    content: str
    author: str
    id: int


class Comment(CommentUpload):
    id: int
    user_id: int

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class Like(BaseModel):
    user_id: int
    video_id: int

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict

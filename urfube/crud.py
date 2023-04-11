import datetime
from urfube.utils import get_hashed_password
from urfube import models, schemas
from peewee import *


def get_user(user_id: int):
    return models.User.get_or_none(models.User.id == user_id)


def get_user_by_username(username: str):
    return models.User.get_or_none(fn.LOWER(models.User.username) == username.lower())


def create_user(user: schemas.UserCreate):
    hashed_password = get_hashed_password(user.password)
    return models.User.create(email=user.email, username=user.username, password=hashed_password)
    # db_user.save()
    # return db_user


def get_video_by_title(title: str):
    return models.Video.get_or_none(models.Video.title == title.lower())


def get_videos():
    return list(models.Video.select())


def add_or_update_history(user: schemas.User, video: schemas.History):
    db_video = models.History.get_or_none(models.History.user == user, models.History.video_id == video.video_id)
    # print(db_video)
    if db_video:
        db_video.update(**video.dict(), user_id=user.id).execute()
    else:
        models.History.create(**video.dict(),
                              user_id=user.id)


def get_user_history(user: schemas.User):
    return list(get_user(user.id).history)


def get_history_by_id(history_id: int):
    return models.History.get_by_id(history_id)


def upload_video(video: schemas.VideoUpload, user: schemas.User):
    link = 'link'
    return models.Video.create(**video.dict(), link=link, user_id=user.id, author=user.username)

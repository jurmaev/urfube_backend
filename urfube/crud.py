import datetime

from peewee import *

from urfube import models, schemas
from urfube.utils import get_hashed_password


def get_user(user_id: int):
    return models.User.get_or_none(models.User.id == user_id)


def get_user_by_username(username: str):
    return models.User.get_or_none(fn.LOWER(models.User.username) == username.lower())


def create_user(user: schemas.UserCreate):
    hashed_password = get_hashed_password(user.password)
    return models.User.create(email=user.email, username=user.username, password=hashed_password)


def get_video_by_title(title: str):
    return models.Video.get_or_none(models.Video.title == title.lower())


def get_videos():
    return list(models.Video.select())


def add_or_update_history(user: schemas.User, video: schemas.History):
    db_video = models.History.get_or_none(models.History.user == user, models.History.video_id == video.video_id)
    if db_video:
        db_video.update(**video.dict(), user_id=user.id).execute()
    else:
        models.History.create(**video.dict(),
                              user_id=user.id)


def get_user_history(user: schemas.User):
    user_history = []
    for history in get_user(user.id).history:
        video = get_video_by_id(history.video_id)
        user_history.append({'video_id': history.video_id, 'timestamp': history.timestamp, 'title': video.title, 'author': video.author,
         'description': video.description})
    return user_history


def get_history_by_id(history_id: int):
    return models.History.get_or_none(models.History.id == history_id)


def upload_video(video: schemas.VideoUpload, user: schemas.User):
    return models.Video.create(**video.dict(), user_id=user.id, author=user.username)


def get_video_by_id(video_id: int):
    return models.Video.get_or_none(models.Video.id == video_id)


def delete_video(video_id: int):
    models.Video.delete_by_id(video_id)


def add_comment(content: str, video_id: int, user: schemas.User):
    models.Comment.create(content=content, video=video_id, user=user)


def delete_comment(comment_id: int):
    models.Comment.delete_by_id(comment_id)


def get_comment_by_id(comment_id: int):
    return models.Comment.get_or_none(models.Comment.id == comment_id)


def edit_comment(comment_id: int, new_content: str):
    models.Comment.update(content=new_content).where(models.Comment.id == comment_id).execute()


def get_comments(video_id: int):
    return [{'content': comment.content, 'author': comment.user.username, 'id': comment.id} for comment in
            list(models.Video.get_by_id(video_id).comments)]


def user_liked_video(user: schemas.User, video_id: int):
    return models.Like.get_or_none(models.Like.video_id == video_id, models.Like.user_id == user)
    # return len(models.Like.select(models.Like.video_id == video_id, models.Like.user_id == user)) == 1


def get_likes(video_id: int):
    return len(list(models.Video.get_by_id(video_id).likes))


def add_like(user: schemas.User, video_id: int):
    models.Like.create(user=user, video=video_id)


def remove_like(user: schemas.User, video_id: int):
    models.Like.delete().where(models.Like.user_id == user, models.Like.video_id == video_id).execute()

import datetime
from peewee import *
from urfube import models, schemas
from urfube.utils import get_hashed_password, create_presigned_url


def get_user(user_id: int):
    return models.User.get_or_none(models.User.id == user_id)


def get_user_by_username(username: str):
    return models.User.get_or_none(fn.LOWER(models.User.username) == username.lower())


def create_user(user: schemas.UserLogin):
    hashed_password = get_hashed_password(user.password)
    return models.User.create(username=user.username, password=hashed_password)


def get_video_by_title(title: str):
    return models.Video.get_or_none(models.Video.title == title.lower())


async def get_videos():
    videos = []
    for video in models.Video.select():
        history = get_history_by_id(video.id)
        timestamp, progress = 0, 0
        if history is not None:
            timestamp = history.timestamp
            progress = round(history.timestamp / history.length, 2)
        video_dict = {'title': video.title, 'id': video.id, 'author': video.author,
                      'user_id': video.user.id,
                      'views': video.views,
                      'created': video.created,
                      'image_link': await create_presigned_url('jurmaev', f'images/{video.id}.jpg'),
                      'profile_link': await create_presigned_url('jurmaev', f'profiles/{video.author}.jpg'),
                      'timestamp': timestamp, 'progress': progress}
        videos.append(video_dict)
    return videos


def add_or_update_history(user: schemas.User, video: schemas.History):
    db_video = models.History.get_or_none(models.History.user == user, models.History.video_id == video.video_id)
    if db_video is not None:
        db_video.update(**video.dict(), user_id=user.id).execute()
    else:
        models.History.create(**video.dict(),
                              user_id=user.id)


async def get_user_history(user: schemas.User):
    user_history = []
    for history in get_user(user.id).history:
        video = get_video_by_id(history.video_id)
        user_history.append(
            {'id': history.video_id, 'timestamp': history.timestamp, 'title': video.title, 'author': video.author,
             'image_link': await create_presigned_url('jurmaev', f'images/{history.video_id}.jpg'),
             'profile_link': await create_presigned_url('jurmaev', f'profiles/{video.author}.jpg'),
             'progress': round(history.timestamp / history.length, 2),
             'views': video.views,
             'created': video.created})
    return user_history


def get_history_by_id(video_id: int):
    return models.History.get_or_none(models.History.id == video_id)


def upload_video(video: schemas.VideoUpload, user: schemas.User):
    return models.Video.create(**video.dict(), user_id=user.id, author=user.username, created=datetime.datetime.now())


def get_video_by_id(video_id: int):
    return models.Video.get_or_none(models.Video.id == video_id)


def delete_video(video_id: int):
    models.Video.delete_by_id(video_id)


def add_comment(content: str, video_id: int, user: schemas.User):
    models.Comment.create(content=content, video=video_id, user=user, created=datetime.datetime.now())


def delete_comment(comment_id: int):
    models.Comment.delete_by_id(comment_id)


def get_comment_by_id(comment_id: int):
    return models.Comment.get_or_none(models.Comment.id == comment_id)


def edit_comment(comment_id: int, new_content: str):
    models.Comment.update(content=new_content).where(models.Comment.id == comment_id).execute()


async def get_comments(video_id: int):
    return [{'content': comment.content, 'author': comment.user.username, 'id': comment.id, 'created': comment.created,
             'profile_link': await create_presigned_url('jurmaev', f'profiles/{comment.user.username}.jpg')}
            for comment in
            list(models.Video.get_by_id(video_id).comments)]


def user_liked_video(user: schemas.User, video_id: int):
    return models.Like.get_or_none(models.Like.video_id == video_id, models.Like.user_id == user)


def get_likes(video_id: int):
    return len(list(models.Video.get_by_id(video_id).likes))


def add_like(user: schemas.User, video_id: int):
    models.Like.create(user=user, video=video_id)


def remove_like(user: schemas.User, video_id: int):
    models.Like.delete().where(models.Like.user_id == user, models.Like.video_id == video_id).execute()


async def get_liked_videos(user: schemas.User):
    liked_videos = []
    for video in user.likes:
        history = get_history_by_id(video.video_id)
        video_info = get_video_by_id(video.video_id)
        liked_videos.append({'id': history.video_id, 'timestamp': history.timestamp, 'title': video_info.title,
                             'author': video_info.author,
                             'image_link': await create_presigned_url('jurmaev', f'images/{history.video_id}.jpg'),
                             'profile_link': await create_presigned_url('jurmaev', f'profiles/{video_info.author}.jpg'),
                             'progress': round(history.timestamp / history.length, 2),
                             'views': video_info.views,
                             'created': video_info.created})
    return liked_videos


def add_view(video_id: int):
    models.Video.update(views=models.Video.views + 1).where(models.Video.id == video_id).execute()


def subscribe(subscriber_id: int, channel_id: int):
    models.Subscription.create(subscriber=subscriber_id, channel=channel_id)


def unsubscribe(subscriber_id: int, channel_id: int):
    models.Subscription.delete().where(models.Subscription.subscriber == subscriber_id,
                                       models.Subscription.channel == channel_id).execute()


def get_subscribers(channel):
    return len(list(channel.subscriptions))


def is_subscribed(user_id: int, channel_id: int):
    return models.Subscription.get_or_none(models.Subscription.subscriber == user_id,
                                           models.Subscription.channel == channel_id) is not None


async def get_channel_info(channel: str):
    user = get_user_by_username(channel)
    return {'channel': channel, 'subscribers': get_subscribers(user), 'videos': user.videos.select().count(),
            'profile_link': await create_presigned_url('jurmaev', f'profiles/{channel}.jpg')}


async def get_channel_videos(channel: schemas.User):
    videos = []
    for video in channel.videos:
        history = get_history_by_id(video.id)
        timestamp, progress = 0, 0
        if history is not None:
            timestamp = history.timestamp
            progress = round(history.timestamp / history.length, 2)
        video_dict = {'title': video.title, 'id': video.id, 'author': video.author,
                      'user_id': video.user.id,
                      'views': video.views,
                      'created': video.created,
                      'image_link': await create_presigned_url('jurmaev', f'images/{video.id}.jpg'),
                      'profile_link': '', 'timestamp': timestamp,
                      'progress': progress}
        videos.append(video_dict)
    return videos


async def get_subscription_videos(user: schemas.User):
    videos = []
    for channel in user.subscribers:
        for video in channel.channel.videos:
            history = get_history_by_id(video.id)
            timestamp, progress = 0, 0
            if history is not None:
                timestamp = history.timestamp
                progress = round(history.timestamp / history.length, 2)
            videos.append({'id': video.id, 'title': video.title,
                           'author': video.author,
                           'image_link': await create_presigned_url('jurmaev', f'images/{video.id}.jpg'),
                           'profile_link': await create_presigned_url('jurmaev', f'profiles/{video.author}.jpg'),
                           'views': video.views,
                           'created': video.created, 'user_id': user.id, 'timestamp': timestamp,
                           'progress': progress})
    return videos

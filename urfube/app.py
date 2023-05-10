import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, List

import fastapi_jsonrpc as jsonrpc
from fastapi import Depends, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt

from urfube import (config, crud, database, dependencies, errors, models,
                    schemas)
from urfube.utils import (create_access_token, create_presigned_url,
                          create_refresh_token, upload_fileobj,
                          verify_password)

origins = ['*']
database.db.connect()
database.db.create_tables(
    [models.User, models.Video, models.History, models.Comment, models.Like, models.Subscription]
)
database.db.close()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def logging_middleware(ctx: jsonrpc.JsonRpcContext):
    logger.info('Request: {request}'.format(request=ctx.raw_request))
    try:
        yield
    finally:
        logger.info('Response: {response}\n'.format(response=ctx.raw_response))


app = jsonrpc.API()
api = jsonrpc.Entrypoint(
    '/api', middlewares=[logging_middleware], tags=['user', 'video', 'history', 'comment', 'like', 'subscriptions']
)
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'],
                   allow_headers=['*'])


@api.method(errors=[errors.UserExistsError], dependencies=[Depends(dependencies.get_db)], tags=['user'])
async def signup(user: schemas.UserCreate):
    db_user = crud.get_user_by_username(user.username)
    if db_user:
        raise errors.UserExistsError
    crud.create_user(user)


@api.method(errors=[errors.WrongUserInfoError],
            dependencies=[Depends(dependencies.get_db)], tags=['user'])
async def login(user: schemas.UserLogin, scopes: list[str] | None = None) -> schemas.Token:
    db_user = crud.get_user_by_username(user.username)
    if not db_user:
        raise errors.WrongUserInfoError
    if not verify_password(user.password, db_user.password):
        raise errors.WrongUserInfoError
    return {
        'access_token': create_access_token(token_data={'sub': user.username, 'scopes': scopes}),
        'refresh_token': create_refresh_token(token_data={'sub': user.username, 'scopes': scopes}),
        'token_type': 'bearer',
    }


@api.method(errors=[], dependencies=[Depends(dependencies.get_db)], tags=['user'])
async def refresh_tokens(refresh_token: str) -> schemas.Token:
    if not refresh_token:
        raise errors.AuthError
    try:
        payload = jwt.decode(refresh_token, config.settings.jwt_refresh_secret_key,
                             algorithms=[config.settings.algorithm])
        username = payload['sub']
        scopes = payload['scopes']
        if username is None:
            raise errors.CredentialsError
        elif datetime.fromtimestamp(payload['exp']) < datetime.now():
            raise errors.ExpirationError
    except(jwt.JWTError, errors.ValidationError):
        raise errors.CredentialsError
    user = crud.get_user_by_username(username)
    if not user:
        raise errors.UserNotFoundError
    return {
        'access_token': create_access_token(token_data={'sub': user.username, 'scopes': scopes}),
        'refresh_token': create_refresh_token(token_data={'sub': user.username, 'scopes': scopes}),
        'token_type': 'bearer',
    }


@app.post('/upload_video/', tags=['video'], dependencies=[Depends(dependencies.get_db)])
async def upload_video(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], video_file: UploadFile,
                       image_file: UploadFile,
                       video_title: str,
                       video_description: str):
    if crud.get_video_by_title(video_title) is not None:
        raise errors.VideoAlreadyExistsError
    db_video = crud.upload_video(schemas.VideoUpload(title=video_title, description=video_description),
                                 user)
    video_upload = await upload_fileobj(video_file.file, 'jurmaev', f'videos/{db_video.id}.mp4', video_file.size)
    image_upload = await upload_fileobj(image_file.file, 'jurmaev', f'images/{db_video.id}.jpg', image_file.size)
    if not video_upload or not image_upload:
        raise errors.VideoUploadFailedError


@api.method(errors=[], dependencies=[Depends(dependencies.get_db)], tags=['video'])
async def get_videos() -> List[schemas.VideoReturn]:
    return await crud.get_videos()


@api.method(errors=[], dependencies=[Depends(dependencies.get_db)], tags=['history'])
async def add_or_update_history(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)],
                                video: schemas.History):
    crud.add_or_update_history(user, video)


@api.method(errors=[], dependencies=[Depends(dependencies.get_db)], tags=['history'])
async def get_user_history(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)]) -> List[
    schemas.HistoryReturn]:
    return await crud.get_user_history(user)


@api.method(errors=[errors.LinkGenerateFailedError], dependencies=[Depends(dependencies.get_db)], tags=['video'])
async def generate_video_link(video_id: int) -> str:
    if crud.get_video_by_id(video_id) is None:
        raise errors.VideoDoesNotExistError
    link = await create_presigned_url('jurmaev', f'videos/{video_id}.mp4')
    if link is None:
        raise errors.LinkGenerateFailedError
    return link


@api.method(errors=[errors.VideoDoesNotExistError], dependencies=[Depends(dependencies.get_db)], tags=['comment'])
async def add_comment(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)],
                      comment: schemas.CommentUpload):
    if crud.get_video_by_id(comment.video_id) is None:
        raise errors.VideoDoesNotExistError
    crud.add_comment(comment.content, comment.video_id, user)


@api.method(errors=[errors.CommentDoesNotExistError], dependencies=[Depends(dependencies.get_db)], tags=['comment'])
async def delete_comment(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], comment_id: int):
    if crud.get_comment_by_id(comment_id) is None:
        raise errors.CommentDoesNotExistError
    crud.delete_comment(comment_id)


@api.method(errors=[errors.CommentDoesNotExistError], dependencies=[Depends(dependencies.get_db)], tags=['comment'])
async def edit_comment(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], comment_id: int,
                       new_content: str):
    if crud.get_comment_by_id(comment_id) is None:
        raise errors.CommentDoesNotExistError
    crud.edit_comment(comment_id, new_content)


@api.method(errors=[errors.VideoDoesNotExistError], dependencies=[Depends(dependencies.get_db)], tags=['comment'])
async def get_comments(video_id: int) -> List[schemas.VideoComment]:
    if crud.get_video_by_id(video_id) is None:
        raise errors.VideoDoesNotExistError
    return crud.get_comments(video_id)


@api.method(errors=[errors.VideoDoesNotExistError], dependencies=[Depends(dependencies.get_db)], tags=['video'])
async def get_video_info(video_id: int) -> schemas.Video:
    db_video = crud.get_video_by_id(video_id)
    if db_video is None:
        raise errors.VideoDoesNotExistError
    return db_video


@api.method(errors=[errors.LikeAlreadyExistsError, errors.VideoDoesNotExistError],
            dependencies=[Depends(dependencies.get_db)], tags=['like'])
async def post_like(
        user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], video_id: int
):
    if crud.get_video_by_id(video_id) is None:
        raise errors.VideoDoesNotExistError
    if crud.user_liked_video(user, video_id) is not None:
        raise errors.LikeAlreadyExistsError
    crud.add_like(user, video_id)


@api.method(errors=[errors.LikeDoesNotExistError, errors.VideoDoesNotExistError],
            dependencies=[Depends(dependencies.get_db)], tags=['like'])
async def remove_like(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], video_id: int):
    if crud.get_video_by_id(video_id) is None:
        raise errors.VideoDoesNotExistError
    if crud.user_liked_video(user, video_id) is None:
        raise errors.LikeDoesNotExistError
    crud.remove_like(user, video_id)


@api.method(errors=[errors.LikeDoesNotExistError, errors.VideoDoesNotExistError],
            dependencies=[Depends(dependencies.get_db)], tags=['like'])
async def get_like(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], video_id: int) -> bool:
    if crud.get_video_by_id(video_id) is None:
        raise errors.VideoDoesNotExistError
    if crud.user_liked_video(user, video_id) is None:
        raise errors.LikeDoesNotExistError
    return crud.user_liked_video(user, video_id) is not None


@api.method(errors=[errors.VideoDoesNotExistError], dependencies=[Depends(dependencies.get_db)],
            tags=['like'])
async def get_likes(video_id: int) -> int:
    if crud.get_video_by_id(video_id) is None:
        raise errors.VideoDoesNotExistError
    return crud.get_likes(video_id)


@api.method(errors=[], dependencies=[Depends(dependencies.get_db)], tags=['like'])
async def get_liked_videos(user: Annotated[schemas.User,
Depends(dependencies.get_auth_user)]) -> List[schemas.HistoryReturn]:
    return await crud.get_liked_videos(user)


@api.method(errors=[errors.VideoDoesNotExistError], dependencies=[Depends(dependencies.get_db)], tags=['video'])
async def post_view(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], video_id: int):
    db_video = crud.get_video_by_id(video_id)
    if db_video is None:
        raise errors.VideoDoesNotExistError
    crud.add_view(video_id)


@api.method(errors=[errors.UserNotFoundError], dependencies=[Depends(dependencies.get_db)], tags=['subscriptions'])
async def subscribe(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], channel: str):
    db_channel = crud.get_user_by_username(channel)
    if db_channel is None:
        raise errors.UserNotFoundError
    crud.subscribe(user.id, db_channel.id)


@api.method(errors=[errors.UserNotFoundError], dependencies=[Depends(dependencies.get_db)], tags=['subscriptions'])
async def unsubscribe(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], channel: str):
    db_channel = crud.get_user_by_username(channel)
    if db_channel is None:
        raise errors.UserNotFoundError
    crud.unsubscribe(user.id, db_channel)


@api.method(errors=[errors.UserNotFoundError], dependencies=[Depends(dependencies.get_db)], tags=['subscriptions'])
async def get_subscribers(channel: str) -> int:
    channel = crud.get_user_by_username(channel)
    if channel is None:
        raise errors.UserNotFoundError
    return crud.get_subscribers(channel)


@api.method(errors=[errors.UserNotFoundError], dependencies=[Depends(dependencies.get_db)], tags=['subscriptions'])
async def is_subscribed(user: Annotated[schemas.User, Depends(dependencies.get_auth_user)], channel: str) -> bool:
    db_channel = crud.get_user_by_username(channel)
    if db_channel is None:
        raise errors.UserNotFoundError
    return crud.is_subscribed(user.id, db_channel.id)


app.bind_entrypoint(api)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run('urfube.app:app', port=5000, access_log=False)

from fastapi.middleware.cors import CORSMiddleware
from typing import List, Annotated
from urfube import database, crud
from urfube.utils import verify_password, create_access_token, create_refresh_token, upload_fileobj, \
    create_presigned_url
from urfube.dependencies import *
from urfube.errors import *
from fastapi import Security, File, UploadFile, Request
import logging
from contextlib import asynccontextmanager
import time

origins = ['*']
database.db.connect()
database.db.create_tables([models.User, models.Video, models.History, models.Comment])
database.db.close()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# handler = logging.FileHandler('urfube/dev.log')
# logger.addHandler(handler)


@asynccontextmanager
async def logging_middleware(ctx: jsonrpc.JsonRpcContext):
    logger.info('Request: %r', ctx.raw_request)
    try:
        yield
    finally:
        logger.info('Response: %r\n', ctx.raw_response)


app = jsonrpc.API()
api = jsonrpc.Entrypoint('/api', middlewares=[logging_middleware], tags=['user', 'videos', 'history', 'comment'])
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'],
                   allow_headers=['*'])


@api.method(errors=[UserExistsError], dependencies=[Depends(get_db)], tags=['user'])
def signup(user: schemas.UserCreate):
    db_user = crud.get_user_by_username(user.username)
    if db_user:
        raise UserExistsError
    crud.create_user(user)


@api.method(errors=[WrongUserInfoError], dependencies=[Depends(get_db)], tags=['user'])
def login(user: schemas.UserLogin, scopes: list[str] | None = None) -> schemas.Token:
    db_user = crud.get_user_by_username(user.username)
    if not db_user:
        raise WrongUserInfoError
    if not verify_password(user.password, db_user.password):
        raise WrongUserInfoError
    return {
        'access_token': create_access_token(token_data={'sub': user.username, 'scopes': scopes}),
        'refresh_token': create_refresh_token(token_data={'sub': user.username, 'scopes': scopes}),
        'token_type': 'bearer',
    }


@api.method(errors=[], dependencies=[Depends(get_db)], tags=['user'])
def refresh_tokens(refresh_token: str) -> schemas.Token:
    if not refresh_token:
        raise AuthError
    try:
        payload = jwt.decode(refresh_token, settings.jwt_refresh_secret_key, algorithms=[settings.algorithm])
        username = payload['sub']
        scopes = payload['scopes']
        if username is None:
            raise CredentialsError
        elif dt.fromtimestamp(payload['exp']) < dt.now():
            raise ExpirationError
    except(jwt.JWTError, ValidationError):
        raise CredentialsError
    user = get_user_by_username(username)
    if not user:
        raise UserNotFoundError
    return {
        'access_token': create_access_token(token_data={'sub': user.username, 'scopes': scopes}),
        'refresh_token': create_refresh_token(token_data={'sub': user.username, 'scopes': scopes}),
        'token_type': 'bearer',
    }


# @api.method(errors=[VideoAlreadyExistsError], dependencies=[Depends(get_db)])
# def upload_video(user: Annotated[schemas.User, Depends(get_auth_user)], video: schemas.VideoUpload) -> schemas.Video:
#     db_video = crud.get_video_by_title(video.title)
#     if db_video:
#         raise VideoAlreadyExistsError
#     # upload_result = upload_file(video_file.filename, 'jurmaev', f'{user.username}/{video_file.filename}')
#     # if not upload_result:
#     #     raise VideoUploadFailedError
#     return crud.upload_video(video, user)


@app.post('/upload_video/', tags=['videos'])
async def upload_video(user: Annotated[schemas.User, Depends(get_auth_user)], file: UploadFile, video_title: str,
                       video_description: str):
    if get_video_by_title(video_title) is not None:
        raise VideoAlreadyExistsError
    db_video = crud.upload_video(schemas.VideoUpload(title=video_title, description=video_description), user)
    upload_result = upload_fileobj(file.file, 'jurmaev', f'{db_video.id}.mp4', file.size)
    if not upload_result:
        raise VideoUploadFailedError


@api.method(errors=[], dependencies=[Depends(get_db)], tags=['videos'])
def get_videos() -> List[schemas.Video]:
    return crud.get_videos()


@api.method(errors=[], dependencies=[Depends(get_db)], tags=['history'])
def add_or_update_history(user: Annotated[schemas.User, Depends(get_auth_user)],
                          video: schemas.History):
    crud.add_or_update_history(user, video)


@api.method(errors=[], dependencies=[Depends(get_db)], tags=['history'])
def get_user_history(user: Annotated[schemas.User, Depends(get_auth_user)]) -> List[schemas.History]:
    return crud.get_user_history(user)


@api.method(errors=[LinkGenerateFailedError], dependencies=[Depends(get_db)], tags=['videos'])
def generate_link(video_id: int) -> str:
    if get_video_by_id(video_id) is None:
        raise VideoDoesNotExistError
    link = create_presigned_url('jurmaev', f'{video_id}.mp4')
    if link is None:
        raise LinkGenerateFailedError
    return link


@api.method(errors=[], dependencies=[Depends(get_db)], tags=['comment'])
def add_comment(user: Annotated[schemas.User, Depends(get_auth_user)], comment: schemas.CommentUpload):
    crud.add_comment(comment.content, comment.video_id, user)


@api.method(errors=[], dependencies=[Depends(get_db)], tags=['comment'])
def delete_comment(user: Annotated[schemas.User, Depends(get_auth_user)], comment_id: int):
    if get_comment_by_id(comment_id) is None:
        raise CommentDoesNotExistError
    crud.delete_comment(comment_id)


@api.method(errors=[], dependencies=[Depends(get_db)], tags=['comment'])
def edit_comment(user: Annotated[schemas.User, Depends(get_auth_user)], comment_id: int, new_content: str):
    if get_comment_by_id(comment_id) is None:
        raise CommentDoesNotExistError
    crud.edit_comment(comment_id, new_content)


app.bind_entrypoint(api)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run('urfube.app:app', port=5000, access_log=False)

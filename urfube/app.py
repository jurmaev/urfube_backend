from fastapi.middleware.cors import CORSMiddleware
from typing import List, Annotated
from urfube import database, crud
from urfube.utils import verify_password, create_access_token, create_refresh_token, upload_file, upload_fileobj
from urfube.dependencies import *
from urfube.errors import *
from fastapi import Security, File, UploadFile
# import aiofiles

origins = ['*']
database.db.connect()
database.db.create_tables([models.User, models.Video])
database.db.close()

app = jsonrpc.API()
api = jsonrpc.Entrypoint('/api')
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'],
                   allow_headers=['*'])


@api.method(errors=[UserExistsError], dependencies=[Depends(get_db)])
def signup(user: schemas.UserCreate) -> str:
    db_user = crud.get_user_by_username(user.username)
    if db_user:
        raise UserExistsError
    return crud.create_user(user).username


@api.method(errors=[WrongUserInfoError], dependencies=[Depends(get_db)])
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


@api.method(errors=[], dependencies=[Depends(get_db)])
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


@app.post('/upload_file/')
async def upload_vid(user: Annotated[schemas.User, Depends(get_auth_user)], file: UploadFile, video: schemas.VideoUpload):
    db_video = crud.get_video_by_title(video.title)
    if db_video:
        raise VideoAlreadyExistsError
    upload_result = upload_fileobj(file.file, 'jurmaev', f'{user.username}/{video.title}')
    if not upload_result:
        raise VideoUploadFailedError
    crud.upload_video(video, user)
    # return video.title


@api.method(errors=[], dependencies=[Depends(get_db)])
def get_videos() -> List[schemas.Video]:
    return crud.get_videos()


@api.method(errors=[], dependencies=[Depends(get_db)])
def add_or_update_history(user: Annotated[schemas.User, Depends(get_auth_user)],
                          video: schemas.History) -> schemas.History:
    return crud.add_or_update_history(user, video)


@api.method(errors=[], dependencies=[Depends(get_db)])
def get_user_history(user: Annotated[schemas.User, Depends(get_auth_user)]) -> List[schemas.History]:
    return crud.get_user_history(user)


app.bind_entrypoint(api)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run('app:app', port=5000, access_log=False)

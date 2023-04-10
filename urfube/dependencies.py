from typing import Annotated
from datetime import datetime as dt
from fastapi import Depends, Header
from jose import jwt
from pydantic import ValidationError
from urfube import schemas, database
from urfube.database import db_state_default
from .errors import *
from .crud import *
from .config import settings
from fastapi.security import SecurityScopes


async def reset_db_state():
    database.db._state._state.set(db_state_default.copy())
    database.db._state.reset()


def get_db(db_state=Depends(reset_db_state)):
    try:
        database.db.connect()
        yield
    finally:
        if not database.db.is_closed():
            database.db.close()


async def get_auth_user(token: str = Header(
    None,
    alias='user-auth-token',
)) -> schemas.User:
    if not token:
        raise AuthError
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.algorithm])
        username = payload['sub']
        if username is None:
            raise CredentialsError
        elif dt.fromtimestamp(payload['exp']) < dt.now():
            raise ExpirationError
        # token_scopes = payload.get('scopes', [])
        # token_data = schemas.TokenData(scopes=token_scopes, username=username)
    except(jwt.JWTError, ValidationError):
        raise CredentialsError
    user = get_user_by_username(username)
    if not user:
        raise UserNotFoundError
    # for scope in security_scopes.scopes:
    #     if scope not in token_data.scopes:
    #         raise MyError(data={'details': 'Not enough permissions'})
    return user


def get_auth_user_scopes(scopes: SecurityScopes, user: Annotated[schemas.User, Depends(get_auth_user)],
                         token: str = Header(
                             None,
                             alias='user-auth-token',
                         )) -> schemas.User:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.algorithm])
    # token_scopes = payload.get('scopes', []) if payload.get('scopes') else []
    token_scopes = payload['scopes']
    token_data = schemas.TokenData(scopes=token_scopes, username=user.username)
    for scope in scopes.scopes:
        if scope not in token_data.scopes:
            raise PermissionError
    return user

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Union, Any
from jose import JWTError, jwt
from urfube.config import settings
from .schemas import *
import boto3
from botocore.exceptions import ClientError
from urfube.errors import S3ClientError

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(token_data: dict, expires_delta: int = None) -> str:
    to_encode = token_data.copy()
    if expires_delta is not None:
        expires_delta = datetime.datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({'exp': expires_delta})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, settings.algorithm)
    return encoded_jwt


def create_refresh_token(token_data: dict, expires_delta: int = None) -> str:
    to_encode = token_data.copy()
    if expires_delta is not None:
        expires_delta = datetime.datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.datetime.utcnow() + timedelta(minutes=settings.refresh_token_expire_minutes)
    to_encode.update({'exp': expires_delta})
    # to_encode = {'exp': expires_delta, 'sub': str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_refresh_secret_key, settings.algorithm)
    return encoded_jwt


def upload_file(file_name, bucket, object_name):
    s3 = boto3.client('s3', endpoint_url='https://storage.yandexcloud.net',
                      aws_access_key_id=settings.aws_access_key_id,
                      aws_secret_access_key=settings.aws_secret_access_key)
    try:
        s3.upload_file(file_name, bucket, object_name)
    except ClientError:
        raise S3ClientError
        return False
    return True


def upload_fileobj(fileobj, bucket, key):
    s3 = boto3.client('s3', endpoint_url='https://storage.yandexcloud.net',
                      aws_access_key_id=settings.aws_access_key_id,
                      aws_secret_access_key=settings.aws_secret_access_key)
    try:
        s3.upload_fileobj(fileobj, bucket, key)
    except ClientError:
        raise S3ClientError
        return False
    return True

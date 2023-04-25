import logging
from datetime import datetime, timedelta
from typing import Any, Union

import boto3
from botocore.exceptions import ClientError
from jose import JWTError, jwt
from passlib.context import CryptContext

from urfube.config import settings
from urfube.schemas import *

# from urfube.app import logger
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


# def upload_file(file_name, bucket, object_name):
#     s3 = boto3.client('s3', endpoint_url='https://storage.yandexcloud.net',
#                       aws_access_key_id=settings.aws_access_key_id,
#                       aws_secret_access_key=settings.aws_secret_access_key)
#     try:
#         s3.upload_file(file_name, bucket, object_name)
#     except ClientError:
#         raise S3ClientError
#         return False
#     return True

class ProgressBar:
    def __init__(self, filesize):
        self.current_value = 0
        self.filesize = filesize

    def upload_progress(self, chunk):
        self.current_value += chunk


def upload_fileobj(fileobj, bucket, key, filesize):
    s3 = boto3.client('s3', endpoint_url='https://storage.yandexcloud.net',
                      aws_access_key_id=settings.aws_access_key_id,
                      aws_secret_access_key=settings.aws_secret_access_key)
    progress_bar = ProgressBar(filesize)

    def upload_progress(chunk):
        progress_bar.upload_progress(chunk)
        logging.info(progress_bar.current_value / progress_bar.filesize)

    try:
        s3.upload_fileobj(fileobj, bucket, key, Callback=upload_progress)
    except ClientError:
        return False
    return True


def create_presigned_url(bucket: str, object_name: str, expiration=3600):
    s3 = boto3.client('s3', endpoint_url='https://storage.yandexcloud.net',
                      aws_access_key_id=settings.aws_access_key_id,
                      aws_secret_access_key=settings.aws_secret_access_key)

    try:
        response = s3.generate_presigned_url('get_object',
                                             Params={'Bucket': bucket,
                                                     'Key': f'{object_name}'},
                                             ExpiresIn=expiration)
    except ClientError:
        # raise S3ClientError
        return None
    return response

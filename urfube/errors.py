import fastapi_jsonrpc as jsonrpc
from pydantic import BaseModel


# class MyError(jsonrpc.BaseError):
#     CODE = 5000
#     MESSAGE = 'My error'
#
#     class DataModel(BaseModel):
#         details: str

class AuthError(jsonrpc.BaseError):
    CODE = 7000
    MESSAGE = 'Auth error'


class CredentialsError(jsonrpc.BaseError):
    CODE = 7001
    MESSAGE = 'Could not validate credentials'


class ExpirationError(jsonrpc.BaseError):
    CODE = 7002
    MESSAGE = 'Token expired'


class PermissionError(jsonrpc.BaseError):
    CODE = 7003
    MESSAGE = 'Not enough permissions'


class UserExistsError(jsonrpc.BaseError):
    CODE = 1000
    MESSAGE = 'User already exists'


class WrongUserInfoError(jsonrpc.BaseError):
    CODE = 1001
    MESSAGE = 'Wrong username or password'


class UserNotFoundError(jsonrpc.BaseError):
    CODE = 1002
    MESSAGE = 'Could not find user'


class VideoAlreadyExistsError(jsonrpc.BaseError):
    CODE = 2000
    MESSAGE = 'Video already exists'

class S3ClientError(jsonrpc.BaseError):
    CODE = 3000
    MESSAGE = 'S3 client error'

class VideoUploadFailedError(jsonrpc.BaseError):
    CODE = 3001
    MESSAGE = 'Video upload failed'
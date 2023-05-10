import fastapi_jsonrpc as jsonrpc
from pydantic import BaseModel


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


# class S3ClientError(jsonrpc.BaseError):
#     CODE = 3000
#     MESSAGE = 'S3 client error'


class VideoUploadFailedError(jsonrpc.BaseError):
    CODE = 3000
    MESSAGE = 'Video upload failed'


class VideoAlreadyExistsError(jsonrpc.BaseError):
    CODE = 3001
    MESSAGE = 'Video already exists'


class VideoDoesNotExistError(jsonrpc.BaseError):
    CODE = 3002
    MESSAGE = 'Video does not exist'


class LinkGenerateFailedError(jsonrpc.BaseError):
    CODE = 3003
    MESSAGE = 'Failed to generate video link'


class CommentDoesNotExistError(jsonrpc.BaseError):
    CODE = 4000
    MESSAGE = 'Comment does not exist'


class LikeAlreadyExistsError(jsonrpc.BaseError):
    CODE = 5000
    MESSAGE = 'Like already exists'


class LikeDoesNotExistError(jsonrpc.BaseError):
    CODE = 5001
    MESSAGE = 'Like does not exist'

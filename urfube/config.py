import pathlib

from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    database_name: str = 'urfube/urfube.db'
    secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    algorithm: str
    jwt_secret_key: str
    jwt_refresh_secret_key: str
    aws_access_key_id: str
    aws_secret_access_key: str

    class Config:
        env_file = f"{pathlib.Path(__file__).resolve().parent}/.env"


settings = Settings()

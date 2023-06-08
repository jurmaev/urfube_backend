import os
import pathlib

from pydantic import BaseSettings


class Settings(BaseSettings):
    database_name: str
    secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    algorithm: str
    jwt_secret_key: str
    jwt_refresh_secret_key: str
    aws_access_key_id: str
    aws_secret_access_key: str
    host: str
    user: str
    password: str
    postgres_port: int

    class Config:
        env_file = f"{pathlib.Path(__file__).resolve().parent}/.env"


settings = Settings()

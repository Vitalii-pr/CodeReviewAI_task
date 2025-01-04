# app/config.py
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    OPENAI_API: str
    GITHUB_ACCESS_TOKEN: str
    REDIS_HOST: str
    REDIS_PORT: int

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


settings = Settings() # type: ignore 

from functools import cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings read from .env

    This should not be instantiated directly. Use the `app_settings()` function.
    """

    development: bool = False
    log_level: str = "info"
    media_dir: str = "./media"
    openai_api_key: str = ""


    class Config:
        env_file = ".env"


@cache
def app_settings() -> Settings:
    """Get application settings"""
    return Settings()

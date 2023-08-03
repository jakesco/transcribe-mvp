from functools import cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings read from .env

    This should not be instantiated directly. Use the `app_settings()` function.
    """

    development: bool = True
    log_level: str = "INFO"
    media: str = "./media"
    job_dump: str = ".jobs"
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


@cache
def app_settings() -> Settings:
    """Get application settings"""
    return Settings()


log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "scribe": {"handlers": ["default"], "level": app_settings().log_level},
    },
}

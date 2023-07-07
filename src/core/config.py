from pydantic import BaseSettings, PostgresDsn
from functools import lru_cache


class Settings(BaseSettings):
    app_title: str = 'url_shortener'
    env_name: str = "URL_SHORTENER"
    base_url: str = "http://localhost:8000"
    db_url: str = "sqlite:///./shortener.db"
    database_dsn: PostgresDsn

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    print(f"Loading settings for: {settings.env_name}")
    return settings

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    ENVIRONMENT: Literal["Local","staging", "production"] = "Local"

    model_config = SettingsConfigDict(
        env_file = "backend/app/envs/.env.local",
        env_ignore_empty=True,
        extra = 'ignore'
    )

    DATABASE_URL: str = ""


settings = Settings()
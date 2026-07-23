from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    secret_key: str = "changeme"

    database_url: str = "postgresql+asyncpg://contextflow:contextflow@localhost:5432/contextflow"

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "changeme"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    ai_provider: Literal["ollama", "openai"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    upload_dir: str = "./uploads"
    max_upload_size_bytes: int = 20 * 1024 * 1024
    allowed_upload_content_types: tuple[str, ...] = (
        "application/pdf",
        "text/plain",
        "text/markdown",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

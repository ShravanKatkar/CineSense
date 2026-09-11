from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env file relative to this file (backend/app/core/config.py)
# Project root is 3 levels up: config.py → core/ → app/ → backend/ → root/
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = Field(
        default="postgresql+asyncpg://cinesense:cinesense@localhost:5432/cinesense"
    )
    tmdb_read_token: SecretStr = Field(default=SecretStr(""))
    tmdb_api_key: SecretStr = Field(default=SecretStr(""))  # TMDB v3 API key
    anthropic_api_key: SecretStr = Field(default=SecretStr(""))
    voyage_api_key: SecretStr = Field(default=SecretStr(""))
    groq_api_key: SecretStr = Field(default=SecretStr(""))
    groq_model: str = Field(default="qwen/qwen3.8-27b")

    jwt_secret_key: SecretStr = Field(
        default=SecretStr("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_minutes: int = Field(default=15)
    refresh_token_days: int = Field(default=7)

    cors_origins: list[str] = Field(default=["http://localhost:5173"])
    daily_llm_budget_usd: float = Field(default=1.00)
    environment: Literal["development", "production", "test"] = Field(default="development")
    app_version: str = Field(default="1.0.0")
    log_level: str = Field(default="INFO")

    # Cache & Background Ingestion Worker (Phase 8)
    redis_url: str | None = Field(default="redis://localhost:6379/0")
    enable_background_sync: bool = Field(default=True)
    tmdb_sync_interval_hours: int = Field(default=6)

    @field_validator("jwt_secret_key")
    @classmethod
    def _validate_jwt_secret_key(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long (e.g. openssl rand -hex 32)")
        return v


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of system Settings."""
    return Settings()

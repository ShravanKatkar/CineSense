from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: PostgresDsn | str = Field(
        default="postgresql+asyncpg://cinesense:cinesense@localhost:5432/cinesense"
    )
    tmdb_read_token: SecretStr = Field(default=SecretStr(""))
    anthropic_api_key: SecretStr = Field(default=SecretStr(""))
    voyage_api_key: SecretStr = Field(default=SecretStr(""))

    jwt_secret_key: SecretStr = Field(
        default=SecretStr("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_minutes: int = Field(default=15)
    refresh_token_days: int = Field(default=7)

    cors_origins: list[str] = Field(default=["http://localhost:5173"])
    daily_llm_budget_usd: float = Field(default=1.00)
    environment: Literal["development", "production", "test"] = Field(default="development")
    log_level: str = Field(default="INFO")

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

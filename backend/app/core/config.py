from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-prod"  # noqa: S105 - dev-only placeholder, rejected in prod


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "staging", "production"] = "development"

    database_url: str = Field(
        default="postgresql+psycopg://stocksense:stocksense@localhost:5432/stocksense"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    cors_origins: str = "http://localhost:3000"

    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    # Fixed-window rate limits for the auth endpoints (per client IP).
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 300
    signup_rate_limit: int = 5
    signup_rate_window_seconds: int = 3600

    market_data_provider: str = "yfinance"
    polygon_api_key: str | None = None
    finnhub_api_key: str | None = None
    alpha_vantage_api_key: str | None = None

    @field_validator("database_url")
    @classmethod
    def _force_psycopg3_driver(cls, v: str) -> str:
        """Hosting providers hand out `postgres://` / `postgresql://`, which
        SQLAlchemy maps to the (uninstalled) psycopg2 driver. Coerce any of those
        to the psycopg3 form so the URL works no matter how it's supplied."""
        for prefix in ("postgresql+psycopg2://", "postgresql://", "postgres://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v

    @model_validator(mode="after")
    def _require_strong_secret_in_prod(self) -> "Settings":
        """Fail fast instead of silently booting production with a forgeable
        JWT secret (the publicly-known default or anything too short for HS256)."""
        if self.environment == "production":
            if self.jwt_secret == _DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET must be set to a random value of at least 32 characters "
                    "in production (e.g. `openssl rand -hex 32`)."
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

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

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

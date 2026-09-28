import logging
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-prod"  # noqa: S105 - dev-only placeholder, rejected in prod

_LOOPBACK_HOSTS = ("@localhost", "@127.0.0.1", "//localhost", "//127.0.0.1")


def _is_loopback(url: str) -> bool:
    """True when the URL points at this machine, where TLS isn't warranted."""
    return any(host in url for host in _LOOPBACK_HOSTS)


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
    # Redis is an optional cache (see app/cache/cache.py): keep the ceiling low
    # so an unreachable instance degrades latency slightly instead of hanging.
    redis_timeout_seconds: float = 2.0

    cors_origins: str = "http://localhost:3000"

    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    # bcrypt work factor. Each +1 doubles hashing time. 12 is a good default on
    # real hardware, but on a shared/throttled free-tier CPU it costs ~1.5s per
    # login. 10 keeps a sane security margin at ~4x the speed. Lowering this
    # does NOT invalidate existing hashes: bcrypt reads the cost from the hash
    # itself, so old passwords keep verifying at whatever cost they were made with.
    bcrypt_rounds: int = Field(default=12, ge=10, le=15)

    # Fixed-window rate limits for the auth endpoints (per client IP).
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 300
    signup_rate_limit: int = 5
    signup_rate_window_seconds: int = 3600

    # Model inference and walk-forward backtests are the two endpoints that cost
    # real CPU per call, on an instance sized for a demo. Authentication already
    # keeps strangers out; these caps keep a single logged-in client (or a stuck
    # retry loop in the UI) from monopolising the box.
    predict_rate_limit: int = 60
    predict_rate_window_seconds: int = 300
    backtest_rate_limit: int = 20
    backtest_rate_window_seconds: int = 300

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
    def _require_tls_to_the_datastores_in_prod(self) -> "Settings":
        """Managed Postgres/Redis are reached over the public internet.

        Credentials and user rows must not cross it in the clear, so require TLS
        in production. Postgres gets `sslmode=require` appended when it is
        missing; Redis can't be fixed up the same way (the scheme itself selects
        TLS, and not every host serves it on the same port), so a plaintext
        `redis://` only warns. Refusing to boot over the *cache* would be
        disproportionate — it carries public market data and rate-limit
        counters, never credentials — and would turn a degraded service into a
        crash loop. Loopback is exempt: that's a developer running production
        settings locally, not an exposed link.
        """
        if self.environment != "production":
            return self

        if not _is_loopback(self.database_url) and "sslmode=" not in self.database_url:
            joiner = "&" if "?" in self.database_url else "?"
            object.__setattr__(
                self, "database_url", f"{self.database_url}{joiner}sslmode=require"
            )

        if self.redis_url.startswith("redis://") and not _is_loopback(self.redis_url):
            logging.getLogger("stocksense.config").warning(
                "REDIS_URL uses plaintext redis:// to a remote host. Prefer the TLS "
                "scheme rediss:// (managed Redis such as Upstash supports it) so cache "
                "traffic isn't readable in transit."
            )

        return self

    @model_validator(mode="after")
    def _reject_wildcard_cors_in_prod(self) -> "Settings":
        """A wildcard origin is incompatible with the credentialed CORS we send.

        The app calls the API with an Authorization header from a different
        origin, so CORSMiddleware runs with allow_credentials=True. Pairing that
        with "*" would let any site on the internet make authenticated
        cross-origin calls on a visitor's behalf. Browsers reject the
        combination outright, so this would fail at runtime anyway — better to
        refuse to boot than to serve a deployment whose frontend silently can't
        talk to it.
        """
        if self.environment == "production" and "*" in self.cors_origins_list:
            raise ValueError(
                'CORS_ORIGINS must list explicit origins in production, not "*" '
                "(credentialed requests cannot use a wildcard). "
                "Example: https://your-app.vercel.app"
            )
        return self

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

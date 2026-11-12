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
    # Lifetime of a session (and of the cookie that carries it). Guests have no
    # password to come back with, so this is how long a guest's watchlist
    # survives between visits. Sessions are rows in the `sessions` table and can
    # be revoked at any time; the cookie's expiry is only the outer bound.
    session_ttl_days: int = 30
    session_cookie_name: str = "ss_session"
    # Secure cookies are refused by browsers over plain http://localhost, so the
    # flag follows the environment. SameSite=Lax is always on: the frontend
    # proxies the API under its own origin, which makes the cookie first-party.
    session_cookie_secure: bool | None = None

    # Email addresses are stored encrypted (AES-256-GCM) with a keyed hash for
    # lookups, so a leaked database dump exposes no addresses. 64 hex chars
    # (`openssl rand -hex 32`). Required in production; a fixed, publicly-known
    # key is used in development so the app runs with no setup.
    email_encryption_key: str | None = None

    # Shared secret the frontend's API proxy attaches to every forwarded request.
    # When it matches, the proxy's X-Client-IP header is trusted for rate
    # limiting (the proxy sits on Vercel, which overwrites X-Forwarded-For with
    # the real client address and cannot be spoofed). Without it the app only
    # trusts the address its own platform's load balancer appends.
    proxy_shared_secret: str | None = None

    # Header the hosting platform's own edge sets to the real client address
    # for requests that reach the backend directly (not via the frontend
    # proxy). Render sits behind Cloudflare, which overwrites
    # `CF-Connecting-IP` on every request, so set it to that there. Leave
    # unset anywhere a client could reach the app without such an edge in
    # front, because then the header is just another client-supplied value.
    trusted_client_ip_header: str | None = None

    # Cloudflare Turnstile (bot protection). Both unset = disabled, which is
    # logged loudly in production. The site key is public (it ships to browsers);
    # the secret key verifies tokens server-side.
    turnstile_site_key: str | None = None
    turnstile_secret_key: str | None = None

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
    # Guest sessions are minted silently on first visit, so this is the cap on
    # how many identities one address can create. Above it the client must
    # pass a Turnstile challenge (when configured) to get another.
    guest_rate_limit: int = 20
    guest_rate_window_seconds: int = 3600

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

    @model_validator(mode="after")
    def _require_email_key_in_prod(self) -> "Settings":
        """Encrypted emails are only as private as the key. Production must
        supply its own; development falls back to a fixed key so `uvicorn`
        just works, at the cost of that key being in the repo."""
        if self.environment == "production" and not self.email_encryption_key:
            raise ValueError(
                "EMAIL_ENCRYPTION_KEY must be set in production "
                "(64 hex characters, e.g. `openssl rand -hex 32`)."
            )
        if self.email_encryption_key is not None:
            try:
                raw = bytes.fromhex(self.email_encryption_key)
            except ValueError:
                raise ValueError("EMAIL_ENCRYPTION_KEY must be hex-encoded") from None
            if len(raw) != 32:
                raise ValueError("EMAIL_ENCRYPTION_KEY must decode to exactly 32 bytes")
        return self

    @model_validator(mode="after")
    def _warn_when_bot_protection_is_off_in_prod(self) -> "Settings":
        if self.environment == "production" and not self.turnstile_secret_key:
            logging.getLogger("stocksense.config").warning(
                "TURNSTILE_SECRET_KEY is not set: bot protection is DISABLED. "
                "Rate limits still apply, but no challenge is ever issued."
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def cookie_secure(self) -> bool:
        if self.session_cookie_secure is not None:
            return self.session_cookie_secure
        return self.environment == "production"

    @property
    def turnstile_enabled(self) -> bool:
        return bool(self.turnstile_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

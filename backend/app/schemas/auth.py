from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    # Reject unknown keys rather than silently dropping them: a request that
    # tries to set a field it doesn't own (say a future `role` or `id`) should
    # fail loudly, not appear to succeed. The User model has no privilege
    # columns today — this keeps that true if one is ever added.
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    # bcrypt only uses the first 72 bytes; cap new passwords there so every
    # character the user types actually contributes to the hash.
    password: str = Field(min_length=8, max_length=72)
    # Cloudflare Turnstile response. Required when Turnstile is configured.
    turnstile_token: str | None = Field(default=None, max_length=4096)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(max_length=128)
    turnstile_token: str | None = Field(default=None, max_length=4096)


class GuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Only needed once the per-IP guest allowance is exhausted.
    turnstile_token: str | None = Field(default=None, max_length=4096)


class UserOut(BaseModel):
    id: str
    email: str | None = None
    is_guest: bool = False
    preferences: dict = {}


class SessionOut(BaseModel):
    """Returned by the sign-in flows. Browsers get the token in an httpOnly
    cookie and should ignore `access_token`; it is there for API clients, which
    send it as `Authorization: Bearer`."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


# Old name, kept so nothing importing it breaks.
Token = SessionOut

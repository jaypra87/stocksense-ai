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


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    id: str
    email: str
    preferences: dict = {}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    # bcrypt only uses the first 72 bytes; cap new passwords there so every
    # character the user types actually contributes to the hash.
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
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

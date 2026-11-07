from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import ORMModel


class UserPublic(ORMModel):
    id: int
    username: str
    avatar_url: str | None = None
    bio: str | None = None
    role: str
    created_at: datetime


class UserPrivate(UserPublic):
    email: EmailStr
    is_active: bool


class UserCreate(ORMModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserUpdate(ORMModel):
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=500)

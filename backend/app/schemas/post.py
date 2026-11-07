from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import ORMModel
from app.schemas.user import UserPublic


class PostRead(ORMModel):
    id: int
    topic_id: int
    author: UserPublic
    content: str
    floor: int
    is_op: bool
    created_at: datetime
    updated_at: datetime


class PostCreate(ORMModel):
    content: str = Field(min_length=1, max_length=20_000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content 不能为空")
        return value


class PostUpdate(ORMModel):
    content: str = Field(min_length=1, max_length=20_000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content 不能为空")
        return value

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.board import BoardBrief
from app.schemas.common import ORMModel
from app.schemas.user import UserPublic


class TopicRead(ORMModel):
    id: int
    title: str
    board: BoardBrief
    author: UserPublic
    is_pinned: bool
    is_locked: bool
    views: int
    reply_count: int
    last_reply_at: datetime | None
    created_at: datetime


class TopicCreate(ORMModel):
    board_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)

    @field_validator("title", "content")
    @classmethod
    def strip_and_reject_blank(cls, value: str, info) -> str:  # noqa: ANN001
        value = value.strip()
        if not value:
            raise ValueError(f"{info.field_name} 不能为空")
        return value


class TopicUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    is_pinned: bool | None = None
    is_locked: bool | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("title 不能为空")
        return value

from pydantic import Field, field_validator

from app.schemas.common import ORMModel


class BoardBrief(ORMModel):
    id: int
    name: str
    slug: str


class BoardRead(BoardBrief):
    description: str
    sort_order: int
    is_active: bool
    topic_count: int


class BoardCreate(ORMModel):
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    description: str = Field(default="", max_length=255)
    sort_order: int = 0

    @field_validator("name", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class BoardUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    slug: str | None = Field(default=None, min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=255)
    sort_order: int | None = None
    is_active: bool | None = None

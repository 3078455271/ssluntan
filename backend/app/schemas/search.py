from typing import Literal

from pydantic import BaseModel

from app.schemas.topic import TopicRead


class SearchMatch(BaseModel):
    """Describe where a topic matched and which floor should be opened."""

    matched_in: Literal["title", "content"]
    post_id: int | None = None
    floor: int | None = None
    snippet: str | None = None


class SearchHit(BaseModel):
    topic: TopicRead
    match: SearchMatch

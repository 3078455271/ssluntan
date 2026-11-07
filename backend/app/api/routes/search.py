from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.schemas.common import Page
from app.schemas.search import SearchHit
from app.services.search import search_topics

router = APIRouter(prefix="/search", tags=["搜索"])


@router.get("", response_model=Page[SearchHit])
async def search(
    db: DbSession,
    q: str = Query(min_length=2, max_length=100, description="搜索关键词"),
    board_id: int | None = Query(default=None, ge=1),
    sort: Literal["relevance", "latest"] = "relevance",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
) -> Page[SearchHit]:
    keyword = q.strip()
    if len(keyword) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="搜索关键词至少需要 2 个非空白字符",
        )

    hits, total = await search_topics(
        db,
        query=keyword,
        board_id=board_id,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return Page[SearchHit].create(hits, total, page, page_size)

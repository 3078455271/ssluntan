from sqlalchemy import ColumnElement, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Board, Post, Topic
from app.schemas.search import SearchHit, SearchMatch
from app.schemas.topic import TopicRead

_LIKE_ESCAPE = "\\"
_SNIPPET_LENGTH = 120


def _escape_like(value: str) -> str:
    """Make user input match literally inside a LIKE pattern."""

    return (
        value.replace(_LIKE_ESCAPE, _LIKE_ESCAPE * 2)
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _build_snippet(content: str, keyword: str) -> str:
    """Return a plain-text, single-line excerpt around the first match."""

    text = " ".join(content.split())
    if len(text) <= _SNIPPET_LENGTH:
        return text

    match_index = text.casefold().find(keyword.casefold())
    if match_index < 0:
        match_index = 0

    start = max(0, match_index - _SNIPPET_LENGTH // 2)
    end = min(len(text), start + _SNIPPET_LENGTH)
    if end - start < _SNIPPET_LENGTH:
        start = max(0, end - _SNIPPET_LENGTH)

    snippet = text[start:end]
    if start > 0:
        snippet = f"…{snippet}"
    if end < len(text):
        snippet = f"{snippet}…"
    return snippet


async def search_topics(
    db: AsyncSession,
    *,
    query: str,
    board_id: int | None = None,
    sort: str = "relevance",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[SearchHit], int]:
    """Search topic titles and every floor, returning one row per topic."""

    keyword = query.strip()
    pattern = f"%{_escape_like(keyword)}%"

    title_hit = Topic.title.ilike(pattern, escape=_LIKE_ESCAPE)
    content_hit = (
        select(Post.id)
        .where(
            Post.topic_id == Topic.id,
            Post.content.ilike(pattern, escape=_LIKE_ESCAPE),
        )
        .exists()
    )
    active_board = (
        select(Board.id)
        .where(Board.id == Topic.board_id, Board.is_active.is_(True))
        .exists()
    )

    filters: list[ColumnElement[bool]] = [active_board]
    if board_id is not None:
        filters.append(Topic.board_id == board_id)
    filters.append(or_(title_hit, content_hit))

    total = (
        await db.scalar(select(func.count()).select_from(Topic).where(*filters))
    ) or 0

    last_activity = func.coalesce(Topic.last_reply_at, Topic.created_at)
    stmt = (
        select(Topic, title_hit.label("title_match"))
        .options(joinedload(Topic.author), joinedload(Topic.board))
        .where(*filters)
    )
    if sort == "relevance":
        stmt = stmt.order_by(
            case((title_hit, 0), else_=1),
            last_activity.desc(),
            Topic.id.desc(),
        )
    else:
        stmt = stmt.order_by(last_activity.desc(), Topic.id.desc())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).unique().all()
    topic_rows = [(row[0], bool(row[1])) for row in rows]

    matched_posts: dict[int, tuple[int, int, str]] = {}
    content_topic_ids = [topic.id for topic, title_matched in topic_rows if not title_matched]
    if content_topic_ids:
        post_stmt = (
            select(Post.topic_id, Post.id, Post.floor, Post.content)
            .where(
                Post.topic_id.in_(content_topic_ids),
                Post.content.ilike(pattern, escape=_LIKE_ESCAPE),
            )
            .order_by(Post.topic_id, Post.floor, Post.id)
        )
        for topic_id, post_id, floor, content in (await db.execute(post_stmt)).all():
            matched_posts.setdefault(topic_id, (post_id, floor, content))

    hits: list[SearchHit] = []
    for topic, title_matched in topic_rows:
        if title_matched:
            match = SearchMatch(matched_in="title")
        else:
            matched = matched_posts.get(topic.id)
            if matched is None:
                # A concurrent deletion can remove the floor between the topic
                # query and the batch lookup; keep the topic result valid.
                match = SearchMatch(matched_in="content")
            else:
                post_id, floor, content = matched
                match = SearchMatch(
                    matched_in="content",
                    post_id=post_id,
                    floor=floor,
                    snippet=_build_snippet(content, keyword),
                )
        hits.append(SearchHit(topic=TopicRead.model_validate(topic), match=match))

    return hits, total

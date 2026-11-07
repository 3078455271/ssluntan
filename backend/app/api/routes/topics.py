from typing import Literal

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Page
from app.schemas.post import PostCreate, PostRead
from app.schemas.topic import TopicCreate, TopicRead, TopicUpdate
from app.services.forum import (
    create_topic,
    delete_topic,
    get_topic,
    increment_views,
    list_posts,
    list_topics,
    reply_to_topic,
    update_topic,
)

router = APIRouter(prefix="/topics", tags=["主题"])


@router.get("", response_model=Page[TopicRead])
async def read_topics(
    db: DbSession,
    board_id: int | None = None,
    q: str | None = Query(default=None, max_length=100),
    sort: Literal["latest", "hot", "new"] = "latest",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[TopicRead]:
    topics, total = await list_topics(
        db,
        board_id=board_id,
        query=q,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    items = [TopicRead.model_validate(topic) for topic in topics]
    return Page[TopicRead].create(items, total, page, page_size)


@router.post("", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
async def create_new_topic(
    payload: TopicCreate,
    db: DbSession,
    user: CurrentUser,
) -> TopicRead:
    topic = await create_topic(db, payload, user)
    return TopicRead.model_validate(topic)


@router.get("/{topic_id}", response_model=TopicRead)
async def read_topic(topic_id: int, db: DbSession) -> TopicRead:
    topic = await get_topic(db, topic_id)
    await increment_views(db, topic)
    return TopicRead.model_validate(topic)


@router.patch("/{topic_id}", response_model=TopicRead)
async def edit_topic(
    topic_id: int,
    payload: TopicUpdate,
    db: DbSession,
    user: CurrentUser,
) -> TopicRead:
    topic = await update_topic(db, topic_id, payload, user)
    return TopicRead.model_validate(topic)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_topic(topic_id: int, db: DbSession, user: CurrentUser) -> None:
    await delete_topic(db, topic_id, user)


@router.get("/{topic_id}/posts", response_model=Page[PostRead])
async def read_posts(
    topic_id: int,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[PostRead]:
    await get_topic(db, topic_id)
    posts, total = await list_posts(db, topic_id, page=page, page_size=page_size)
    items = [PostRead.model_validate(post) for post in posts]
    return Page[PostRead].create(items, total, page, page_size)


@router.post("/{topic_id}/posts", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_reply(
    topic_id: int,
    payload: PostCreate,
    db: DbSession,
    user: CurrentUser,
) -> PostRead:
    post = await reply_to_topic(db, topic_id, payload.content, user)
    return PostRead.model_validate(post)

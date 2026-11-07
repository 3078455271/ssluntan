from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import can_manage, is_moderator
from app.models import Board, Post, Topic, User
from app.schemas.board import BoardCreate, BoardUpdate
from app.schemas.post import PostUpdate
from app.schemas.topic import TopicCreate, TopicUpdate


async def list_boards(db: AsyncSession, include_inactive: bool = False) -> list[Board]:
    stmt = select(Board).order_by(Board.sort_order, Board.id)
    if not include_inactive:
        stmt = stmt.where(Board.is_active.is_(True))
    return list((await db.scalars(stmt)).all())


async def get_board(db: AsyncSession, board_id: int) -> Board:
    board = await db.get(Board, board_id)
    if board is None:
        raise NotFoundError("版块不存在")
    return board


async def get_board_by_slug(db: AsyncSession, slug: str) -> Board:
    board = await db.scalar(select(Board).where(Board.slug == slug))
    if board is None:
        raise NotFoundError("版块不存在")
    return board


async def create_board(db: AsyncSession, payload: BoardCreate) -> Board:
    board = Board(**payload.model_dump())
    db.add(board)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("版块名称或 slug 已存在") from exc
    await db.refresh(board)
    return board


async def update_board(db: AsyncSession, board_id: int, payload: BoardUpdate) -> Board:
    board = await get_board(db, board_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(board, key, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("版块名称或 slug 已存在") from exc
    await db.refresh(board)
    return board


async def list_topics(
    db: AsyncSession,
    *,
    board_id: int | None = None,
    query: str | None = None,
    sort: str = "latest",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Topic], int]:
    filters = []
    if board_id is not None:
        filters.append(Topic.board_id == board_id)
    if query:
        filters.append(Topic.title.ilike(f"%{query.strip()}%"))

    total = await db.scalar(select(func.count()).select_from(Topic).where(*filters)) or 0

    stmt = (
        select(Topic)
        .options(joinedload(Topic.author), joinedload(Topic.board))
        .where(*filters)
    )
    if sort == "hot":
        stmt = stmt.order_by(Topic.is_pinned.desc(), Topic.views.desc(), Topic.created_at.desc())
    elif sort == "new":
        stmt = stmt.order_by(Topic.is_pinned.desc(), Topic.created_at.desc())
    else:
        stmt = stmt.order_by(
            Topic.is_pinned.desc(),
            func.coalesce(Topic.last_reply_at, Topic.created_at).desc(),
        )

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    topics = list((await db.scalars(stmt)).unique().all())
    return topics, total


async def get_topic(db: AsyncSession, topic_id: int) -> Topic:
    stmt = (
        select(Topic)
        .options(joinedload(Topic.author), joinedload(Topic.board))
        .where(Topic.id == topic_id)
    )
    topic = await db.scalar(stmt)
    if topic is None:
        raise NotFoundError("主题不存在")
    return topic


async def list_posts(
    db: AsyncSession, topic_id: int, *, page: int = 1, page_size: int = 20
) -> tuple[list[Post], int]:
    total = (
        await db.scalar(select(func.count()).select_from(Post).where(Post.topic_id == topic_id))
        or 0
    )
    stmt = (
        select(Post)
        .options(joinedload(Post.author))
        .where(Post.topic_id == topic_id)
        .order_by(Post.floor)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    posts = list((await db.scalars(stmt)).unique().all())
    return posts, total


async def get_post(db: AsyncSession, post_id: int) -> Post:
    stmt = (
        select(Post)
        .options(joinedload(Post.author), joinedload(Post.topic))
        .where(Post.id == post_id)
    )
    post = await db.scalar(stmt)
    if post is None:
        raise NotFoundError("帖子不存在")
    return post


async def create_topic(db: AsyncSession, payload: TopicCreate, author: User) -> Topic:
    board = await get_board(db, payload.board_id)
    if not board.is_active:
        raise NotFoundError("版块不存在")

    now = datetime.now(UTC)
    topic = Topic(
        title=payload.title,
        board=board,
        author=author,
        last_reply_at=now,
    )
    topic.posts.append(
        Post(content=payload.content, author=author, floor=1, is_op=True)
    )
    board.topic_count += 1
    db.add(topic)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("主题创建失败，请重试") from exc

    return await get_topic(db, topic.id)


async def reply_to_topic(
    db: AsyncSession, topic_id: int, content: str, author: User
) -> Post:
    topic = await get_topic(db, topic_id)
    if topic.is_locked:
        raise ConflictError("主题已锁定，不能回复")

    max_floor = (
        await db.scalar(select(func.max(Post.floor)).where(Post.topic_id == topic.id)) or 0
    )
    post = Post(
        topic_id=topic.id,
        author_id=author.id,
        content=content,
        floor=max_floor + 1,
    )
    db.add(post)
    topic.reply_count += 1
    topic.last_reply_at = datetime.now(UTC)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("楼层冲突，请重试") from exc

    return await get_post(db, post.id)


async def update_topic(
    db: AsyncSession, topic_id: int, payload: TopicUpdate, actor: User
) -> Topic:
    topic = await get_topic(db, topic_id)
    if not can_manage(actor.role, actor.id, topic.author_id):
        raise ForbiddenError("没有权限修改该主题")

    data = payload.model_dump(exclude_unset=True)
    if ("is_pinned" in data or "is_locked" in data) and not is_moderator(actor.role):
        raise ForbiddenError("只有管理员可以置顶或锁定主题")

    for key, value in data.items():
        setattr(topic, key, value)
    await db.commit()
    return await get_topic(db, topic_id)


async def delete_topic(db: AsyncSession, topic_id: int, actor: User) -> None:
    topic = await get_topic(db, topic_id)
    if not can_manage(actor.role, actor.id, topic.author_id):
        raise ForbiddenError("没有权限删除该主题")

    topic.board.topic_count = max(0, topic.board.topic_count - 1)
    await db.delete(topic)
    await db.commit()


async def update_post(
    db: AsyncSession, post_id: int, payload: PostUpdate, actor: User
) -> Post:
    post = await get_post(db, post_id)
    if not can_manage(actor.role, actor.id, post.author_id):
        raise ForbiddenError("没有权限修改该帖子")
    post.content = payload.content
    await db.commit()
    return await get_post(db, post_id)


async def delete_post(db: AsyncSession, post_id: int, actor: User) -> None:
    post = await get_post(db, post_id)
    if not can_manage(actor.role, actor.id, post.author_id):
        raise ForbiddenError("没有权限删除该帖子")
    if post.is_op:
        raise ConflictError("不能单独删除楼主帖，请删除整个主题")

    post.topic.reply_count = max(0, post.topic.reply_count - 1)
    await db.delete(post)
    await db.commit()


async def increment_views(db: AsyncSession, topic: Topic) -> None:
    topic.views += 1
    await db.commit()

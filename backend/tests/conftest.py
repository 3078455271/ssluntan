from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_db
from app.main import app
from app.models import Base, Board, Post, Topic, User


@pytest_asyncio.fixture
async def session_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Create a throwaway SQLite database so tests never touch forum.db."""

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            yield http
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def forum(session_factory: async_sessionmaker[AsyncSession]) -> dict[str, Any]:
    """Seed a small forum with title, content, hidden-board and escaping cases."""

    now = datetime.now(UTC)
    async with session_factory() as session:
        alice = User(username="alice", email="alice@example.com", password_hash="x")
        bob = User(username="bob", email="bob@example.com", password_hash="x")
        general = Board(name="综合讨论", slug="general", sort_order=1)
        hidden = Board(name="隐藏版块", slug="hidden", sort_order=2, is_active=False)
        session.add_all([alice, bob, general, hidden])
        await session.flush()

        def make_topic(
            title: str,
            board: Board,
            author: User,
            replies: list[tuple[User, str]],
            *,
            age_minutes: int = 0,
        ) -> Topic:
            topic = Topic(
                title=title,
                board=board,
                author=author,
                last_reply_at=now - timedelta(minutes=age_minutes),
            )
            topic.posts.append(
                Post(content=f"{title} 的首帖内容。", author=author, floor=1, is_op=True)
            )
            for index, (reply_author, content) in enumerate(replies, start=2):
                topic.posts.append(
                    Post(content=content, author=reply_author, floor=index)
                )
            topic.reply_count = len(replies)
            session.add(topic)
            return topic

        title_topic = make_topic(
            "FastAPI 入门指南",
            general,
            alice,
            [(bob, "感谢分享，FastAPI 很好用。")],
            age_minutes=30,
        )
        content_topic = make_topic(
            "周末闲聊",
            general,
            bob,
            [
                (alice, "大家最近在做什么？"),
                (alice, "我在学 fastapi，感觉不错。"),
                (bob, "fastapi 的依赖注入很香。"),
            ],
        )
        hidden_topic = make_topic(
            "秘密版块",
            hidden,
            alice,
            [(bob, "fastapi 隐藏内容")],
        )
        percent_topic = make_topic("100% 完成", general, alice, [])
        decoy_percent_topic = make_topic("1000 完成", general, bob, [])
        underscore_topic = make_topic("a_b 命名", general, alice, [])
        decoy_underscore_topic = make_topic("axb 命名", general, bob, [])

        await session.commit()

    return {
        "board_general": general.id,
        "board_hidden": hidden.id,
        "title_topic": title_topic.id,
        "content_topic": content_topic.id,
        "hidden_topic": hidden_topic.id,
        "percent_topic": percent_topic.id,
        "decoy_percent_topic": decoy_percent_topic.id,
        "underscore_topic": underscore_topic.id,
        "decoy_underscore_topic": decoy_underscore_topic.id,
    }

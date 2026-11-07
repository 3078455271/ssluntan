from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Board

DEFAULT_BOARDS = [
    {
        "name": "综合讨论",
        "slug": "general",
        "description": "什么都可以聊，先读版规。",
        "sort_order": 10,
    },
    {
        "name": "技术交流",
        "slug": "tech",
        "description": "Python、Web、后端与工程实践。",
        "sort_order": 20,
    },
    {
        "name": "站务反馈",
        "slug": "meta",
        "description": "论坛功能建议、Bug 反馈与公告。",
        "sort_order": 30,
    },
]


async def seed_default_boards(db: AsyncSession) -> None:
    for item in DEFAULT_BOARDS:
        exists = await db.scalar(select(Board).where(Board.slug == item["slug"]))
        if exists is None:
            db.add(Board(**item))
    await db.commit()

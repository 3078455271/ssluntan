"""将已有账号提升为管理员。

用法（在 backend/ 目录下）：
    uv run python -m scripts.promote_admin alice
"""

import argparse
import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.models import User

# 管理命令只输出结果；开发环境开启的 SQL echo 在这里没有意义。
engine.echo = False


async def promote(username: str) -> int:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.username == username))
        if user is None:
            print(f"未找到用户：{username}")
            return 1
        if user.role == "admin":
            print(f"{username} 已经是管理员")
            return 0

        user.role = "admin"
        await db.commit()
        print(f"已将 {username} 提升为管理员")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="将已有用户设置为管理员")
    parser.add_argument("username", help="已注册的用户名")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(promote(args.username)))


if __name__ == "__main__":
    main()

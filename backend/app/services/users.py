from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.core.security import hash_password, verify_dummy_password, verify_password
from app.models import User
from app.schemas.user import UserCreate


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(func.lower(User.username) == username.strip().lower())
    return await db.scalar(stmt)


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    username = payload.username.strip().lower()
    email = str(payload.email).strip().lower()

    exists_stmt = select(User).where(
        or_(func.lower(User.username) == username, func.lower(User.email) == email)
    )
    if await db.scalar(exists_stmt):
        raise ConflictError("用户名或邮箱已被注册")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("用户名或邮箱已被注册") from exc

    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, identifier: str, password: str) -> User | None:
    identifier = identifier.strip().lower()
    stmt = select(User).where(
        or_(func.lower(User.username) == identifier, func.lower(User.email) == identifier)
    )
    user = await db.scalar(stmt)

    if user is None:
        verify_dummy_password(password)
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

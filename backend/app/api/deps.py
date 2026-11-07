from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User
from app.services.users import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def _resolve_api_user(db: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None

    user_id = decode_access_token(token)
    if user_id is None:
        return None

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        return None
    return user


async def get_current_api_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录状态无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = await _resolve_api_user(db, token)
    if user is None:
        raise credentials_error
    return user


async def get_optional_api_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User | None:
    """Resolve a user when a token is present, without rejecting anonymous requests."""
    return await _resolve_api_user(db, token)


CurrentUser = Annotated[User, Depends(get_current_api_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_api_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


AdminUser = Annotated[User, Depends(require_admin)]

import secrets
from typing import Annotated

from fastapi import Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.csrf import valid_csrf_token
from app.core.database import get_db
from app.core.errors import ForbiddenError
from app.core.security import decode_access_token
from app.models import User
from app.services.users import get_user_by_id


async def get_web_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    user: User | None = None

    if token:
        user_id = decode_access_token(token)
        if user_id is not None:
            user = await get_user_by_id(db, user_id)
            if user is not None and not user.is_active:
                user = None

    request.state.current_user = user
    return user


WebUser = Annotated[User | None, Depends(get_web_user)]


async def csrf_protect(
    request: Request,
    csrf_token: Annotated[str, Form()],
) -> None:
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    if not cookie_token or not csrf_token:
        raise ForbiddenError("CSRF 校验失败，请刷新页面后重试")
    if not valid_csrf_token(cookie_token) or not secrets.compare_digest(cookie_token, csrf_token):
        raise ForbiddenError("CSRF 校验失败，请刷新页面后重试")

import math

from fastapi.responses import Response

from app.core.config import settings


def page_count(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size))


def safe_next_redirect(value: str, default: str = "/") -> str:
    if value.startswith("/") and not value.startswith("//"):
        return value
    return default


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )

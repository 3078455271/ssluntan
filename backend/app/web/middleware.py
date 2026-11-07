from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings
from app.core.csrf import CSRF_MAX_AGE_SECONDS, new_csrf_token, valid_csrf_token


class CsrfCookieMiddleware(BaseHTTPMiddleware):
    """Ensure every browser has a signed CSRF token cookie and expose it to templates."""

    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(settings.csrf_cookie_name)
        needs_cookie = False

        if not token or not valid_csrf_token(token):
            token = new_csrf_token()
            needs_cookie = True

        request.state.csrf_token = token
        response = await call_next(request)

        if needs_cookie:
            response.set_cookie(
                settings.csrf_cookie_name,
                token,
                max_age=CSRF_MAX_AGE_SECONDS,
                httponly=True,
                samesite="lax",
                secure=settings.cookie_secure,
                path="/",
            )
        return response

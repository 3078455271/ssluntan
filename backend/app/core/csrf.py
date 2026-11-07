import secrets

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import settings

serializer = URLSafeTimedSerializer(settings.secret_key, salt="forum-csrf")

CSRF_MAX_AGE_SECONDS = 60 * 60 * 2


def new_csrf_token() -> str:
    return serializer.dumps(secrets.token_urlsafe(24))


def valid_csrf_token(token: str, max_age: int = CSRF_MAX_AGE_SECONDS) -> bool:
    try:
        serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return False
    return True

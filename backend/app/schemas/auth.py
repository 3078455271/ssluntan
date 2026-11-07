from pydantic import BaseModel

from app.schemas.user import UserPrivate


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenWithUser(Token):
    user: UserPrivate

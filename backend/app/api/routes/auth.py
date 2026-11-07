from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import TokenWithUser
from app.schemas.user import UserCreate, UserPrivate
from app.services.users import authenticate, create_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbSession) -> UserPrivate:
    user = await create_user(db, payload)
    return UserPrivate.model_validate(user)


@router.post("/login", response_model=TokenWithUser)
async def login(
    db: DbSession,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenWithUser:
    user = await authenticate(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)
    return TokenWithUser(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserPrivate.model_validate(user),
    )


@router.get("/me", response_model=UserPrivate)
async def read_me(user: CurrentUser) -> UserPrivate:
    return UserPrivate.model_validate(user)

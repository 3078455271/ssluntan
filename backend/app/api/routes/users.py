from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import NotFoundError
from app.models import User
from app.schemas.user import UserPrivate, UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=UserPrivate)
async def read_current_user(user: CurrentUser) -> UserPrivate:
    return UserPrivate.model_validate(user)


@router.patch("/me", response_model=UserPrivate)
async def update_current_user(
    payload: UserUpdate,
    user: CurrentUser,
    db: DbSession,
) -> UserPrivate:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return UserPrivate.model_validate(user)


@router.get("/{username}", response_model=UserPublic)
async def read_user(username: str, db: DbSession) -> UserPublic:
    user = await db.scalar(
        select(User).where(User.username == username.strip().lower())
    )
    if user is None:
        raise NotFoundError("用户不存在")
    return UserPublic.model_validate(user)

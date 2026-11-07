from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.post import PostRead, PostUpdate
from app.services.forum import delete_post, update_post

router = APIRouter(prefix="/posts", tags=["帖子"])


@router.patch("/{post_id}", response_model=PostRead)
async def edit_post(
    post_id: int,
    payload: PostUpdate,
    db: DbSession,
    user: CurrentUser,
) -> PostRead:
    post = await update_post(db, post_id, payload, user)
    return PostRead.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_post(post_id: int, db: DbSession, user: CurrentUser) -> None:
    await delete_post(db, post_id, user)

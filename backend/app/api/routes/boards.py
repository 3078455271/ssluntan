from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AdminUser, DbSession, OptionalUser, oauth2_scheme
from app.core.errors import ForbiddenError
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.services.forum import (
    create_board,
    get_board,
    get_board_by_slug,
    list_boards,
    update_board,
)

router = APIRouter(prefix="/boards", tags=["版块"])


@router.get("", response_model=list[BoardRead])
async def read_boards(
    db: DbSession,
    user: OptionalUser,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    include_inactive: bool = Query(default=False),
) -> list[BoardRead]:
    if include_inactive:
        if token is None:
            raise ForbiddenError("需要管理员权限查看已停用版块")
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录状态无效或已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.role != "admin":
            raise ForbiddenError("需要管理员权限查看已停用版块")
    boards = await list_boards(db, include_inactive=include_inactive)
    return [BoardRead.model_validate(board) for board in boards]


@router.get("/{slug}", response_model=BoardRead)
async def read_board(slug: str, db: DbSession) -> BoardRead:
    board = await get_board_by_slug(db, slug)
    return BoardRead.model_validate(board)


@router.post("", response_model=BoardRead, status_code=status.HTTP_201_CREATED)
async def create_new_board(
    payload: BoardCreate,
    db: DbSession,
    _admin: AdminUser,
) -> BoardRead:
    board = await create_board(db, payload)
    return BoardRead.model_validate(board)


@router.patch("/{board_id}", response_model=BoardRead)
async def edit_board(
    board_id: int,
    payload: BoardUpdate,
    db: DbSession,
    _admin: AdminUser,
) -> BoardRead:
    board = await update_board(db, board_id, payload)
    return BoardRead.model_validate(board)


@router.get("/id/{board_id}", response_model=BoardRead, include_in_schema=False)
async def read_board_by_id(board_id: int, db: DbSession) -> BoardRead:
    board = await get_board(db, board_id)
    return BoardRead.model_validate(board)

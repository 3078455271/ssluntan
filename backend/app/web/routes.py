import math
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import create_access_token
from app.schemas.topic import TopicCreate
from app.schemas.user import UserCreate
from app.services.forum import (
    create_topic,
    get_board_by_slug,
    get_topic,
    increment_views,
    list_boards,
    list_posts,
    list_topics,
    reply_to_topic,
)
from app.services.users import authenticate, create_user
from app.web.deps import WebUser, csrf_protect
from app.web.routes_helpers import page_count, safe_next_redirect, set_session_cookie
from app.web.templating import render

router = APIRouter(include_in_schema=False)

Db = Annotated[AsyncSession, Depends(get_db)]
Csrf = Annotated[None, Depends(csrf_protect)]


@router.get("/")
async def home(request: Request, user: WebUser, db: Db):
    boards = await list_boards(db)
    topics, _ = await list_topics(db, page_size=10)
    return render(
        request,
        "index.html",
        {"boards": boards, "topics": topics},
    )


@router.get("/boards/{slug}")
async def board_page(
    request: Request,
    slug: str,
    user: WebUser,
    db: Db,
    page: int = Query(default=1, ge=1),
):
    board = await get_board_by_slug(db, slug)
    topics, total = await list_topics(db, board_id=board.id, page=page, page_size=20)
    return render(
        request,
        "board.html",
        {
            "board": board,
            "topics": topics,
            "total": total,
            "page": page,
            "pages": page_count(total, 20),
            "base_url": f"/boards/{board.slug}",
        },
    )


async def _topic_context(
    request: Request,
    db: AsyncSession,
    topic_id: int,
    *,
    page: int = 1,
    error: str | None = None,
) -> dict:
    topic = await get_topic(db, topic_id)
    await increment_views(db, topic)
    posts, total = await list_posts(db, topic_id, page=page, page_size=20)
    return {
        "topic": topic,
        "posts": posts,
        "total": total,
        "page": page,
        "pages": page_count(total, 20),
        "base_url": f"/topics/{topic.id}",
        "error": error,
    }


@router.get("/topics/new")
async def new_topic_page(
    request: Request,
    user: WebUser,
    db: Db,
    board_id: int | None = None,
):
    if user is None:
        return RedirectResponse("/login?next=/topics/new", status_code=303)
    boards = await list_boards(db)
    return render(
        request,
        "new_topic.html",
        {"boards": boards, "board_id": board_id, "error": None, "form": {}},
    )


@router.get("/topics/{topic_id}")
async def topic_page(
    request: Request,
    topic_id: int,
    user: WebUser,
    db: Db,
    page: int = Query(default=1, ge=1),
):
    return render(request, "topic.html", await _topic_context(request, db, topic_id, page=page))


@router.get("/login")
async def login_page(request: Request, user: WebUser, next: str = "/"):
    if user is not None:
        return RedirectResponse("/", status_code=303)
    return render(request, "login.html", {"next": safe_next_redirect(next), "error": None})


@router.post("/login")
async def login_submit(
    request: Request,
    user: WebUser,
    db: Db,
    _csrf: Csrf,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    next: Annotated[str, Form()] = "/",
):
    account = await authenticate(db, username, password)
    if account is None:
        return render(
            request,
            "login.html",
            {"next": safe_next_redirect(next), "error": "用户名或密码错误"},
            status_code=401,
        )

    response = RedirectResponse(safe_next_redirect(next), status_code=303)
    set_session_cookie(response, create_access_token(account.id))
    return response


@router.get("/register")
async def register_page(request: Request, user: WebUser):
    if user is not None:
        return RedirectResponse("/", status_code=303)
    return render(request, "register.html", {"error": None, "form": {}})


@router.post("/register")
async def register_submit(
    request: Request,
    user: WebUser,
    db: Db,
    _csrf: Csrf,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    form = {"username": username, "email": email}
    try:
        payload = UserCreate(username=username, email=email, password=password)
        account = await create_user(db, payload)
    except (ValidationError, AppError) as exc:
        error = exc.detail if isinstance(exc, AppError) else _first_validation_error(exc)
        return render(
            request,
            "register.html",
            {"error": error, "form": form},
            status_code=400,
        )

    response = RedirectResponse("/", status_code=303)
    set_session_cookie(response, create_access_token(account.id))
    return response


@router.post("/logout")
async def logout(_csrf: Csrf):
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response


@router.post("/topics/new")
async def new_topic_submit(
    request: Request,
    user: WebUser,
    db: Db,
    _csrf: Csrf,
    board_id: Annotated[int, Form()],
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
):
    if user is None:
        return RedirectResponse("/login?next=/topics/new", status_code=303)

    boards = await list_boards(db)
    form = {"board_id": board_id, "title": title, "content": content}
    try:
        payload = TopicCreate(board_id=board_id, title=title, content=content)
        topic = await create_topic(db, payload, user)
    except (ValidationError, AppError) as exc:
        error = exc.detail if isinstance(exc, AppError) else _first_validation_error(exc)
        return render(
            request,
            "new_topic.html",
            {"boards": boards, "board_id": board_id, "error": error, "form": form},
            status_code=400,
        )

    return RedirectResponse(f"/topics/{topic.id}", status_code=303)


@router.post("/topics/{topic_id}/reply")
async def reply_submit(
    request: Request,
    topic_id: int,
    user: WebUser,
    db: Db,
    _csrf: Csrf,
    content: Annotated[str, Form()],
):
    if user is None:
        return RedirectResponse(f"/login?next=/topics/{topic_id}", status_code=303)

    content = content.strip()
    if not content:
        return render(
            request,
            "topic.html",
            await _topic_context(request, db, topic_id, error="回复内容不能为空"),
            status_code=400,
        )

    try:
        post = await reply_to_topic(db, topic_id, content, user)
    except AppError as exc:
        return render(
            request,
            "topic.html",
            await _topic_context(request, db, topic_id, error=exc.detail),
            status_code=exc.status_code,
        )

    target_page = math.ceil((post.floor) / 20)
    return RedirectResponse(
        f"/topics/{topic_id}?page={target_page}#floor-{post.floor}",
        status_code=303,
    )


def _first_validation_error(exc: ValidationError) -> str:
    first = exc.errors()[0]
    message = first.get("msg", "输入不合法")
    location = ".".join(str(part) for part in first.get("loc", ()))
    return f"{location}: {message}" if location else message

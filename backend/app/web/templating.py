from datetime import datetime
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import BASE_DIR, settings

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


templates.env.filters["dt"] = _format_datetime
templates.env.globals["app_name"] = settings.app_name


def render(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    status_code: int = 200,
):
    ctx: dict[str, Any] = {
        "request": request,
        "current_user": getattr(request.state, "current_user", None),
        "csrf_token": getattr(request.state, "csrf_token", ""),
    }
    if context:
        ctx.update(context)
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=ctx,
        status_code=status_code,
    )

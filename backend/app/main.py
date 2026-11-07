from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.errors import AppError
from app.services.seed import seed_default_boards


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Prepare the database on startup for local development."""

    if settings.auto_create_tables:
        await init_db()
    if settings.seed_default_data:
        async with SessionLocal() as session:
            await seed_default_boards(session)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="SSluntan 论坛后端 API，前端通过 Vite 独立运行。",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "message": "请求参数校验失败"},
        )

    app.include_router(api_router)

    if settings.enable_legacy_web_ui:
        # 旧的服务端渲染页面，仅用于兼容；前后端分离部署时保持关闭。
        from app.web.middleware import CsrfCookieMiddleware
        from app.web.routes import router as web_router

        app.add_middleware(CsrfCookieMiddleware)
        app.include_router(web_router)
    else:

        @app.get("/", include_in_schema=False)
        async def root() -> dict[str, str]:
            return {
                "name": settings.app_name,
                "status": "ok",
                "docs": "/docs",
                "api": settings.api_prefix,
            }

    return app


app = create_app()

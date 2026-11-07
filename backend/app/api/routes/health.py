from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings

router = APIRouter(tags=["系统"])


@router.get("/health")
async def health(db: DbSession) -> dict[str, str]:
    """Liveness probe that also verifies the database connection."""

    await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }

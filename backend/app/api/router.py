from fastapi import APIRouter

from app.api.routes import auth, boards, health, posts, search, topics, users
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(boards.router)
api_router.include_router(search.router)
api_router.include_router(topics.router)
api_router.include_router(posts.router)

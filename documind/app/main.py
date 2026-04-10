# app/main.py — replace entire file

from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from loguru import logger


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    from app.settings import get_settings
    from app.core.database import init_engine, dispose_engine
    settings = get_settings()

    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"[{settings.environment}]"
    )

    if settings.environment != "testing":
        init_engine(settings.database_url)

    if settings.environment != "testing":
        try:
            from app.modules.rag.repository import VectorRepository
            repo = VectorRepository(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                collection_name=settings.rag_collection_name,
                dimension=settings.embedding_dimension,
            )
            await repo.ensure_collection()
        except Exception as e:
            logger.warning(f"Qdrant not available: {e}")

    yield

    if settings.environment != "testing":
        await dispose_engine()

    logger.info(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    # All imports INSIDE function — prevents module-level
    # caching before test overrides are registered
    from app.settings import get_settings
    from app.exceptions import register_exception_handlers
    from app.middleware import register_middleware
    from app.modules.health.router import router as health_router
    from app.modules.documents.router import (
        router as documents_router
    )
    from app.modules.rag.router import router as rag_router
    from app.modules.chat.router import router as chat_router
    from app.modules.conversations.router import (
        router as conversations_router
    )
    from app.modules.auth.router import (    # NEW
        router as auth_router
    )
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="RAG-powered document intelligence service",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    register_middleware(app)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router)  
    app.include_router(documents_router)
    app.include_router(rag_router)
    app.include_router(chat_router)
    app.include_router(conversations_router)

    return app


# ── IMPORTANT ─────────────────────────────────────────────────────
# Do NOT call create_app() here at module level.
# uvicorn needs it so we use a factory string instead:
# uvicorn app.main:create_app --factory --reload
#
# For direct import compatibility we expose app lazily:
def get_app() -> FastAPI:
    return create_app()
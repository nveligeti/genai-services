# app/main.py
# Chapter 2: Application factory pattern + onion architecture
# Chapter 5: Lifespan for async startup/shutdown

from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from loguru import logger


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Import here — NOT at module level
    from app.settings import get_settings
    settings = get_settings()

    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"[{settings.environment}]"
    )
    yield
    logger.info(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    # Import here — NOT at module level
    from app.settings import get_settings
    from app.exceptions import register_exception_handlers
    from app.middleware import register_middleware
    from app.modules.health.router import router as health_router

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

    return app


app = create_app()
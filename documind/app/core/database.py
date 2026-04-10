# app/core/database.py
# Chapter 7: async SQLAlchemy engine and session management

from collections.abc import AsyncGenerator
from typing import Annotated
from fastapi import Depends
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
import sys

# Windows event loop fix for psycopg async
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base.
    All ORM models inherit from this.
    Chapter 7: single base for all entities.
    """
    pass


# Module-level engine — initialized in lifespan
_engine = None
_async_session_factory = None


def init_engine(database_url: str) -> None:
    """
    Initialize async engine.
    Called during lifespan startup (Chapter 5).
    """
    global _engine, _async_session_factory

    _engine = create_async_engine(
        database_url,
        echo=False,        # set True for SQL debug logging
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    logger.info("Database engine initialized")


async def dispose_engine() -> None:
    """Dispose engine on shutdown (Chapter 5: lifespan)."""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("Database engine disposed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — yields async DB session.
    Chapter 7: session factory with setup/teardown.
    Chapter 11: used as fixture in integration tests.
    """
    if _async_session_factory is None:
        raise RuntimeError(
            "Database engine not initialized. "
            "Call init_engine() first."
        )

    async with _async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Annotated dependency for clean injection
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

# app/core/database.py — add entities import at bottom
# so Base.metadata includes all tables

# Add this at the very end of database.py:

def import_all_entities() -> None:
    """
    Import all entities to register them with Base.metadata.
    Called before create_all() in tests and migrations.
    """
    from app.core import entities          # noqa: F401
    from app.modules.auth import entities  # noqa: F401
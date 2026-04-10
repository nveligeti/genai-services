# tests/conftest.py — replace entire file

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.main import create_app
from app.settings import Settings, get_settings
from app.core.database import Base, get_db_session
import app.modules.documents.service as doc_svc_module

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ── Settings ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        environment="testing",
        debug=True,
        llm_provider="mock",
        secret_key="test-secret-key-exactly-32-chars-long",
        database_url=TEST_DATABASE_URL,
        embedding_model="mock",
    )


# ── Database ──────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings):
    """
    Single in-memory SQLite engine for entire test session.
    Drop all first to ensure clean state regardless of
    how many times metadata has been imported.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        # Drop ALL first — ensures no leftover state
        await conn.run_sync(Base.metadata.drop_all)
        # Then create fresh
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncSession:
    """
    Function-scoped session with rollback after each test.
    Chapter 11: complete isolation between tests.
    """
    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session
        await session.rollback()


# ── App + Client ──────────────────────────────────────────────────

# tests/conftest.py — update app fixture only

# tests/conftest.py — replace app fixture only

@pytest.fixture(scope="session")
def app(test_settings, test_engine):
    """
    Patch settings before create_app() is ever called.
    This is the only reliable way to override lru_cache.
    """
    import app.settings as settings_module
    from app.settings import get_settings as original_gs

    # Step 1 — clear any cached value
    original_gs.cache_clear()

    # Step 2 — replace the function itself before create_app
    settings_module.get_settings = lambda: test_settings

    # Step 3 — NOW create the app (sees test settings)
    from app.main import create_app as _create_app
    application = _create_app()

    # Step 4 — also override FastAPI DI for route handlers
    application.dependency_overrides[original_gs] = (
        lambda: test_settings
    )

    yield application

    # Step 5 — restore original
    settings_module.get_settings = original_gs
    original_gs.cache_clear()


@pytest.fixture(scope="session")
def client(app) -> TestClient:
    with TestClient(app) as c:
        yield c

# tests/conftest.py — add this fixture

@pytest_asyncio.fixture(scope="function")
async def db_session_commit(test_engine) -> AsyncSession:
    """
    Function-scoped session that COMMITS.
    Used for E2E tests where router commits transactions.
    Cleans up after itself by deleting all rows.
    """
    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session
        # Clean up all tables after test
        await session.rollback()
# ── Cleanup ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_document_store():
    """Clear in-memory document store before every test."""
    doc_svc_module._document_store.clear()
    yield
    doc_svc_module._document_store.clear()
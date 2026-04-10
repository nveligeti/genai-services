# tests/conftest.py — replace entire file

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
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
    """Single in-memory SQLite engine for entire test session."""
    from app.core import entities           # noqa: F401
    from app.modules.auth import entities   # noqa: F401

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(test_engine):
    """
    Session-scoped factory shared across all tests.
    Used to supply sessions to the FastAPI DI override.
    """
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(session_factory) -> AsyncSession:
    """
    Function-scoped session with rollback after each test.
    Chapter 11: complete isolation between tests.
    """
    async with session_factory() as session:
        yield session
        await session.rollback()


# ── App + Client ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app(test_settings, test_engine, session_factory):
    """
    Test application with all dependency overrides.
    Overrides get_db_session globally so ALL tests
    use the test SQLite engine — never calls init_engine().
    """
    import app.settings as settings_module
    from app.settings import get_settings as original_gs
    original_gs.cache_clear()

    # Patch settings before create_app
    settings_module.get_settings = lambda: test_settings

    from app.main import create_app as _create_app
    application = _create_app()

    # Override settings dependency
    application.dependency_overrides[original_gs] = (
        lambda: test_settings
    )

    # ── Override DB session globally ──────────────────────────────
    # This is the key fix — replaces get_db_session for ALL routes
    # so no route ever calls init_engine() during tests
    async def override_db_session():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    application.dependency_overrides[get_db_session] = (
        override_db_session
    )

    yield application

    settings_module.get_settings = original_gs
    original_gs.cache_clear()


@pytest.fixture(scope="session")
def client(app) -> TestClient:
    with TestClient(app) as c:
        yield c


# ── Cleanup ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_document_store():
    """Clear in-memory document store before every test."""
    doc_svc_module._document_store.clear()
    yield
    doc_svc_module._document_store.clear()


# ── Auth helpers ──────────────────────────────────────────────────

@pytest.fixture
def registered_user(client: TestClient) -> dict:
    """Register a fresh test user per test."""
    import uuid
    # Use unique email per test to avoid duplicate conflicts
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "securepassword123",
        },
    )
    return {
        "email": unique_email,
        "password": "securepassword123",
        "user": response.json(),
    }


@pytest.fixture
def auth_token(client: TestClient, registered_user) -> str:
    """Login and return bearer token."""
    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Authorization headers for protected requests."""
    return {"Authorization": f"Bearer {auth_token}"}
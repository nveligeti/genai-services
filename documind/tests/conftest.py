# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from app.settings import Settings, get_settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        environment="testing",
        debug=True,
        llm_provider="mock",
        secret_key="test-secret-key-exactly-32-chars-long",
        database_url="sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture(scope="session")
def app(test_settings: Settings):
    # Step 1 — clear any cached real settings
    get_settings.cache_clear()

    # Step 2 — monkey-patch get_settings BEFORE create_app() is called
    # This ensures even module-level calls inside create_app() get test settings
    import app.settings as settings_module
    original_get_settings = settings_module.get_settings

    def mock_get_settings() -> Settings:
        return test_settings

    settings_module.get_settings = mock_get_settings

    # Step 3 — now create the app (all get_settings() calls see test settings)
    from app.main import create_app
    application = create_app()

    # Step 4 — also register FastAPI dependency override for route handlers
    application.dependency_overrides[original_get_settings] = mock_get_settings

    yield application

    # Step 5 — restore original after session
    settings_module.get_settings = original_get_settings
    original_get_settings.cache_clear()


@pytest.fixture(scope="session")
def client(app) -> TestClient:
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clear_document_store():
    """
    Clear in-memory document store before every test.
    Chapter 11: test isolation — shared mutable state reset.
    Prevents documents from one test appearing in another.
    """
    import app.modules.documents.service as svc
    svc._document_store.clear()
    yield
    svc._document_store.clear()
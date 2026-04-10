# tests/e2e/test_conversations.py
# Chapter 11: E2E tests for conversation endpoints

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.core.database import get_db_session


# tests/e2e/test_conversations.py — update override fixture
@pytest.fixture(autouse=True)
def auth(app):
    """Bypass auth for conversation tests."""
    from app.modules.auth.dependencies import (
        get_current_user,
        get_admin_user,
    )
    from app.modules.auth.schemas import AuthenticatedUser

    mock_user = AuthenticatedUser(
        user_id="test-user-id",
        email="test@example.com",
        role="ADMIN",      # ADMIN so delete works too
        token_id="test-token-id",
    )
    app.dependency_overrides[get_current_user] = (
        lambda: mock_user
    )
    app.dependency_overrides[get_admin_user] = (
        lambda: mock_user
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_admin_user, None)
    
# @pytest.fixture(autouse=True)
# def override_db(app, db_session):
#     """
#     Override DB session for E2E conversation tests.
#     Uses autoflush session so router commits work correctly.
#     """
#     from app.core.database import get_db_session

#     async def override():
#         yield db_session

#     app.dependency_overrides[get_db_session] = override
#     yield
#     app.dependency_overrides.pop(get_db_session, None)


class TestConversationEndpoints:

    def test_create_conversation_returns_201(
        self, client: TestClient
    ):
        response = client.post(
            "/conversations",
            json={"title": "Test Chat"},
        )
        assert response.status_code == 201

    def test_create_conversation_response_contract(
        self, client: TestClient
    ):
        """Chapter 11: contract assertion."""
        response = client.post(
            "/conversations",
            json={"title": "My Chat"},
        )
        data = response.json()

        assert "id" in data
        assert "title" in data
        assert "created_at" in data
        assert data["title"] == "My Chat"
        assert data["is_active"] is True

    def test_get_conversation_returns_messages(
        self, client: TestClient
    ):
        """
        E2E: vertical test — create then retrieve.
        Chapter 11: two endpoints working together.
        """
        # Create
        create = client.post(
            "/conversations",
            json={"title": "Chat with messages"},
        )
        conv_id = create.json()["id"]

        # Retrieve
        get = client.get(f"/conversations/{conv_id}")
        assert get.status_code == 200
        assert get.json()["id"] == conv_id
        assert "messages" in get.json()

    def test_get_nonexistent_conversation_returns_404(
        self, client: TestClient
    ):
        """Chapter 11: boundary — 404 for missing resource."""
        response = client.get("/conversations/nonexistent")
        assert response.status_code == 404

    def test_list_conversations(self, client: TestClient):
        """E2E: list endpoint contract."""
        client.post(
            "/conversations", json={"title": "Chat 1"}
        )
        client.post(
            "/conversations", json={"title": "Chat 2"}
        )

        response = client.get("/conversations")
        assert response.status_code == 200
        data = response.json()

        assert "conversations" in data
        assert "total" in data
        assert isinstance(data["conversations"], list)

    def test_delete_conversation_returns_204(
        self, client: TestClient
    ):
        """Chapter 11: verify delete status code."""
        create = client.post(
            "/conversations", json={"title": "To Delete"}
        )
        conv_id = create.json()["id"]

        delete = client.delete(f"/conversations/{conv_id}")
        assert delete.status_code == 204

    def test_deleted_conversation_not_retrievable(
        self, client: TestClient
    ):
        """
        E2E: horizontal test — create, delete, verify gone.
        Chapter 11: verify side effect end to end.
        """
        create = client.post(
            "/conversations", json={"title": "Delete Me"}
        )
        conv_id = create.json()["id"]

        client.delete(f"/conversations/{conv_id}")

        get = client.get(f"/conversations/{conv_id}")
        assert get.status_code == 404
# tests/e2e/test_chat.py — replace the autouse fixture

import json
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.modules.rag.schemas import RAGQueryResponse
from app.modules.chat.router import get_rag_pipeline

@pytest.fixture(autouse=True)
def auth(app):
    """Bypass auth for chat tests."""
    from app.modules.auth.dependencies import get_current_user
    from app.modules.auth.schemas import AuthenticatedUser

    mock_user = AuthenticatedUser(
        user_id="test-user-id",
        email="test@example.com",
        role="USER",
        token_id="test-token-id",
    )
    app.dependency_overrides[get_current_user] = (
        lambda: mock_user
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)
    
@pytest.fixture(autouse=True)
def mock_rag_pipeline(app):
    """
    Override RAG pipeline dependency at FastAPI app level.
    Chapter 11: use dependency_overrides not monkeypatch
    for FastAPI DI system.
    """
    mock_pipeline = AsyncMock()
    mock_pipeline.query = AsyncMock(
        return_value=RAGQueryResponse(
            query="test",
            results=[],
            total_results=0,
            context="No relevant context found in documents.",
        )
    )

    # Override at app level — this is what FastAPI actually uses
    app.dependency_overrides[get_rag_pipeline] = (
        lambda: mock_pipeline
    )

    yield mock_pipeline

    # Clean up override after each test
    app.dependency_overrides.pop(get_rag_pipeline, None)


class TestChatEndpoint:

    def test_non_streaming_chat_returns_200(
        self, client: TestClient
    ):
        """MFT — chat endpoint reachable."""
        response = client.post(
            "/chat",
            json={"message": "What is FastAPI?"},
        )
        assert response.status_code == 200

    def test_non_streaming_response_contract(
        self, client: TestClient
    ):
        """
        E2E: contract assertion.
        Chapter 11: nonbrittle — fields not exact values.
        """
        response = client.post(
            "/chat",
            json={"message": "What is FastAPI?"},
        )
        data = response.json()

        assert "message" in data
        assert "rag_context_used" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert len(data["message"]) > 0

    def test_non_streaming_rejects_empty_message(
        self, client: TestClient
    ):
        """Chapter 11: invalid data boundary test."""
        response = client.post(
            "/chat",
            json={"message": ""},
        )
        assert response.status_code == 422

    def test_streaming_endpoint_returns_event_stream(
        self, client: TestClient
    ):
        """
        E2E: SSE endpoint returns correct content type.
        Chapter 6: text/event-stream header required.
        """
        with client.stream(
            "POST",
            "/chat/stream",
            json={"message": "What is FastAPI?"},
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in (
                response.headers.get("content-type", "")
            )

    def test_streaming_produces_parseable_sse_events(
        self, client: TestClient
    ):
        """
        E2E: SSE events must be valid JSON.
        Chapter 6: data: {json} format.
        """
        events = []
        with client.stream(
            "POST",
            "/chat/stream",
            json={"message": "Hello"},
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    events.append(event)

        assert len(events) > 0
        for event in events:
            assert "type" in event
            assert "content" in event

    def test_streaming_event_sequence(
        self, client: TestClient
    ):
        """
        E2E: verify event ordering.
        Chapter 6: rag → token(s) → done.
        """
        event_types = []
        with client.stream(
            "POST",
            "/chat/stream",
            json={"message": "Hello", "use_rag": False},
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    event_types.append(event["type"])

        assert event_types[0] == "rag"
        assert event_types[-1] == "done"
        assert "token" in event_types

    def test_streaming_with_rag_disabled(
        self, client: TestClient
    ):
        """E2E: use_rag=False skips retrieval."""
        events = []
        with client.stream(
            "POST",
            "/chat/stream",
            json={"message": "Hello", "use_rag": False},
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    events.append(event)

        rag_event = next(
            (e for e in events if e["type"] == "rag"), None
        )
        assert rag_event is not None
        assert rag_event["metadata"]["rag_used"] is False

    @pytest.mark.parametrize("message", [
        "What is FastAPI?",
        "Hello!",
        "Explain RAG in simple terms",
    ])
    def test_streaming_handles_various_prompts(
        self, client: TestClient, message: str
    ):
        """IT — stream works for different prompt types."""
        with client.stream(
            "POST",
            "/chat/stream",
            json={"message": message, "use_rag": False},
        ) as response:
            assert response.status_code == 200
            lines = list(response.iter_lines())
            data_lines = [
                l for l in lines if l.startswith("data: ")
            ]
            assert len(data_lines) > 0
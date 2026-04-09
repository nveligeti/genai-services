# tests/e2e/test_rag.py
# Chapter 11: E2E tests for RAG endpoints

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


class TestRAGQueryEndpoint:

    def test_query_endpoint_exists(self, client: TestClient):
        """MFT — endpoint must be reachable."""
        with patch(
            "app.modules.rag.pipeline.RAGPipeline.query",
            new_callable=AsyncMock,
        ) as mock_query:
            from app.modules.rag.schemas import RAGQueryResponse
            mock_query.return_value = RAGQueryResponse(
                query="test",
                results=[],
                total_results=0,
                context="No relevant context found in documents.",
            )
            response = client.post(
                "/rag/query",
                json={"query": "What is FastAPI?"},
            )
        assert response.status_code == 200

    def test_query_response_contract(self, client: TestClient):
        """
        E2E: response must contain required fields.
        Chapter 11: contract assertion.
        """
        with patch(
            "app.modules.rag.pipeline.RAGPipeline.query",
            new_callable=AsyncMock,
        ) as mock_query:
            from app.modules.rag.schemas import RAGQueryResponse
            mock_query.return_value = RAGQueryResponse(
                query="What is FastAPI?",
                results=[],
                total_results=0,
                context="No relevant context found.",
            )
            response = client.post(
                "/rag/query",
                json={"query": "What is FastAPI?"},
            )

        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total_results" in data
        assert "context" in data

    def test_query_rejects_empty_string(self, client: TestClient):
        """
        Boundary test — empty query rejected.
        Chapter 11: invalid data test.
        Chapter 4: min_length=1 validation.
        """
        response = client.post(
            "/rag/query",
            json={"query": ""},
        )
        assert response.status_code == 422

    def test_query_rejects_limit_over_10(self, client: TestClient):
        """
        Boundary test — limit must be 1-10.
        Chapter 11: boundary at maximum.
        """
        response = client.post(
            "/rag/query",
            json={"query": "test", "limit": 11},
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("limit", [1, 5, 10])
    def test_query_accepts_valid_limits(
        self, client: TestClient, limit: int
    ):
        """
        Chapter 11: parametrize valid boundary values.
        """
        with patch(
            "app.modules.rag.pipeline.RAGPipeline.query",
            new_callable=AsyncMock,
        ) as mock_query:
            from app.modules.rag.schemas import RAGQueryResponse
            mock_query.return_value = RAGQueryResponse(
                query="test",
                results=[],
                total_results=0,
                context="No context.",
            )
            response = client.post(
                "/rag/query",
                json={"query": "test", "limit": limit},
            )
        assert response.status_code == 200
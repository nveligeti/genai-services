# tests/e2e/test_health.py
# Chapter 11: Vertical E2E tests for the health endpoint
# Tests behavior (contract) not implementation

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """
    E2E tests for /health endpoint.

    Chapter 11 patterns used:
    - Contract-based assertions (not exact values)
    - Middleware side effect verification
    - Nonbrittle test design
    """

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health endpoint must always be reachable."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_is_json(self, client: TestClient) -> None:
        """Response must be valid JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        assert response.json() is not None

    def test_health_response_contract(self, client: TestClient) -> None:
        """
        Response must contain all required fields.
        Chapter 11: contract assertion — not exact values.
        """
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "environment" in data

    def test_health_status_is_healthy(self, client: TestClient) -> None:
        """Status field must always be 'healthy'."""
        response = client.get("/health")
        assert response.json()["status"] == "healthy"

    def test_health_environment_reflects_test_override(
        self, client: TestClient
    ) -> None:
        """
        Environment must reflect test settings dependency override.
        Chapter 11: verifies DI override works correctly.
        """
        response = client.get("/health")
        assert response.json()["environment"] == "testing"

    def test_health_includes_request_id_header(
        self, client: TestClient
    ) -> None:
        """
        Middleware must attach X-Request-ID to every response.
        Chapter 11: verify middleware side effect.
        """
        response = client.get("/health")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) == 32  # hex UUID

    def test_health_includes_response_time_header(
        self, client: TestClient
    ) -> None:
        """
        Middleware must attach X-Response-Time to every response.
        Chapter 11: verify middleware side effect.
        """
        response = client.get("/health")
        assert "x-response-time" in response.headers
        duration = float(response.headers["x-response-time"])
        assert duration >= 0

    def test_health_request_id_is_unique_per_request(
        self, client: TestClient
    ) -> None:
        """
        Each request must receive a unique request ID.
        Chapter 11: invariance test — IDs must never repeat.
        """
        response1 = client.get("/health")
        response2 = client.get("/health")

        id1 = response1.headers["x-request-id"]
        id2 = response2.headers["x-request-id"]

        assert id1 != id2

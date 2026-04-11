# tests/e2e/test_auth.py
# Chapter 11: E2E auth tests

import pytest
from fastapi.testclient import TestClient


class TestRegistration:

    def test_register_returns_201(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": "new@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201

    def test_register_response_contract(self, client: TestClient):
        """Chapter 11: contract — no password in response."""
        response = client.post(
            "/auth/register",
            json={
                "email": "contract@example.com",
                "password": "password123",
            },
        )
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "role" in data
        assert "hashed_password" not in data   # never exposed
        assert "password" not in data

    def test_duplicate_email_rejected(self, client: TestClient):
        """Chapter 11: boundary — duplicate email."""
        client.post(
            "/auth/register",
            json={
                "email": "dup@example.com",
                "password": "password123",
            },
        )
        response = client.post(
            "/auth/register",
            json={
                "email": "dup@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    def test_weak_password_rejected(self, client: TestClient):
        """Chapter 11: boundary — min_length=8."""
        response = client.post(
            "/auth/register",
            json={
                "email": "weak@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_invalid_email_rejected(self, client: TestClient):
        """Chapter 11: invalid data — bad email format."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
            },
        )
        assert response.status_code == 422


class TestLogin:

    def test_login_returns_token(
        self, client: TestClient, registered_user
    ):
        """Chapter 11: happy path — valid credentials."""
        response = client.post(
            "/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(
        self, client: TestClient, registered_user
    ):
        """
        Chapter 11: boundary — wrong password.
        Chapter 8: 401 not 403.
        """
        response = client.post(
            "/auth/login",
            json={
                "email": registered_user["email"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    def test_unknown_email_returns_401(
        self, client: TestClient
    ):
        """Chapter 8: prevents user enumeration."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401


class TestProtectedEndpoints:

    def test_no_token_returns_401(self, client: TestClient):
        """Chapter 11: boundary — missing auth header."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_invalid_token_returns_401(
        self, client: TestClient
    ):
        """Chapter 11: boundary — malformed token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    def test_valid_token_accesses_me(
        self, client: TestClient, auth_headers
    ):
        """Chapter 11: happy path — authenticated access."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert "email" in response.json()


# tests/e2e/test_auth.py — find the test_rbac_admin_endpoint
# and make sure it is INDENTED inside the TestLogout class

class TestLogout:

    def test_logout_returns_204(
        self, client: TestClient, auth_headers
    ):
        response = client.post(
            "/auth/logout", headers=auth_headers
        )
        assert response.status_code == 204

    def test_token_rejected_after_logout(
        self, client: TestClient, registered_user
    ):
        login = client.post(
            "/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        before = client.get("/auth/me", headers=headers)
        assert before.status_code == 200

        client.post("/auth/logout", headers=headers)

        after = client.get("/auth/me", headers=headers)
        assert after.status_code == 401


    @pytest.mark.parametrize("role,expected_status", [
        ("USER",  403),
        ("ADMIN", 404),
    ])
    def test_rbac_admin_endpoint(
        self,
        client: TestClient,
        role: str,
        expected_status: int,
    ):
        """
        Chapter 8: RBAC — USER vs ADMIN access.
        USER  → 403 (authenticated but not authorized)
        ADMIN → 404 (authorized but conversation not found)
        """
        import uuid
        email = (
            f"rbac_{role.lower()}_{uuid.uuid4().hex[:6]}"
            f"@example.com"
        )

        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "password123",
                "role": role,
            },
        )

        login = client.post(
            "/auth/login",
            json={"email": email, "password": "password123"},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Use guaranteed nonexistent UUID
        nonexistent_id = uuid.uuid4().hex

        response = client.delete(
            f"/conversations/{nonexistent_id}",
            headers=headers,
        )
        assert response.status_code == expected_status
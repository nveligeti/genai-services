# tests/unit/test_auth_service.py
# Chapter 11: unit tests for security functions

import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.exceptions import UnauthorizedException


class TestPasswordHashing:

    def test_hash_is_not_plain_text(self):
        """Chapter 8: password must never be stored plain."""
        hashed = hash_password("mysecretpassword")
        assert hashed != "mysecretpassword"

    def test_same_password_produces_different_hashes(self):
        """
        Chapter 8: bcrypt auto-salting invariance.
        Chapter 11: invariance test.
        """
        h1 = hash_password("mysecretpassword")
        h2 = hash_password("mysecretpassword")
        assert h1 != h2   # different salts each time

    def test_correct_password_verifies(self):
        """Chapter 11: happy path."""
        hashed = hash_password("mysecretpassword")
        assert verify_password("mysecretpassword", hashed) is True

    def test_wrong_password_fails_verification(self):
        """Chapter 11: invalid data boundary test."""
        hashed = hash_password("mysecretpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password_fails_verification(self):
        """Chapter 11: boundary — empty string."""
        hashed = hash_password("mysecretpassword")
        assert verify_password("", hashed) is False


class TestJWTTokens:

    def test_token_has_three_parts(self):
        """Chapter 8: header.payload.signature format."""
        token = create_access_token(
            user_id="user123",
            token_id="token123",
            role="USER",
        )
        parts = token.split(".")
        assert len(parts) == 3

    def test_decoded_token_contains_correct_claims(self):
        """Chapter 11: verify claims preserved."""
        token = create_access_token(
            user_id="user123",
            token_id="token456",
            role="ADMIN",
        )
        claims = decode_access_token(token)

        assert claims["user_id"] == "user123"
        assert claims["token_id"] == "token456"
        assert claims["role"] == "ADMIN"

    def test_tampered_token_raises_unauthorized(self):
        """
        Chapter 11: security boundary test.
        Chapter 8: signature verification.
        """
        token = create_access_token(
            user_id="user123",
            token_id="token123",
            role="USER",
        )
        # Tamper with the payload section
        parts = token.split(".")
        parts[1] = parts[1] + "tampered"
        tampered = ".".join(parts)

        with pytest.raises(UnauthorizedException):
            decode_access_token(tampered)

    def test_expired_token_raises_unauthorized(self):
        """
        Chapter 11: boundary — expired token rejected.
        Chapter 8: exp claim enforced.
        """
        from datetime import timedelta
        token = create_access_token(
            user_id="user123",
            token_id="token123",
            role="USER",
            expires_delta=timedelta(seconds=-1),  # already expired
        )
        with pytest.raises(UnauthorizedException):
            decode_access_token(token)

    def test_invalid_token_string_raises_unauthorized(self):
        """Chapter 11: invalid data test."""
        with pytest.raises(UnauthorizedException):
            decode_access_token("not.a.valid.token")
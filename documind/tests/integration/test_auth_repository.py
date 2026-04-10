# tests/integration/test_auth_repository.py
# Chapter 11: integration tests for auth repositories

import pytest
from app.modules.auth.entities import TokenEntity, UserEntity
from app.modules.auth.repository import (
    TokenRepository,
    UserRepository,
)
from app.core.security import hash_password
from datetime import datetime, timedelta, timezone


class TestUserRepository:

    @pytest.mark.asyncio
    async def test_create_and_get_user(self, db_session):
        """Integration — create then retrieve."""
        repo = UserRepository(db_session)
        user = UserEntity(
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        created = await repo.create(user)

        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.email == "test@example.com"
        assert fetched.role == "USER"
        assert fetched.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session):
        """Integration — email lookup."""
        repo = UserRepository(db_session)
        user = UserEntity(
            email="findme@example.com",
            hashed_password=hash_password("password123"),
        )
        await repo.create(user)

        fetched = await repo.get_by_email("findme@example.com")
        assert fetched is not None
        assert fetched.email == "findme@example.com"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_returns_none(
        self, db_session
    ):
        """Chapter 11: boundary — missing record."""
        repo = UserRepository(db_session)
        result = await repo.get_by_id("nonexistent")
        assert result is None


class TestTokenRepository:

    @pytest.mark.asyncio
    async def test_revoke_token(self, db_session):
        """
        Integration — token revocation.
        Chapter 8: logout invalidates token.
        """
        user_repo = UserRepository(db_session)
        token_repo = TokenRepository(db_session)

        user = UserEntity(
            email="revoke@example.com",
            hashed_password=hash_password("password123"),
        )
        await user_repo.create(user)

        from datetime import timezone
        token = TokenEntity(
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        await token_repo.create(token)

        # Should be active
        active = await token_repo.get_active_token(token.id)
        assert active is not None

        # Revoke
        revoked = await token_repo.revoke(token.id)
        assert revoked is True

        # Should now be inactive
        result = await token_repo.get_active_token(token.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_expired_token_not_returned(self, db_session):
        """
        Integration — expired tokens filtered out.
        Chapter 11: boundary test.
        """
        user_repo = UserRepository(db_session)
        token_repo = TokenRepository(db_session)

        user = UserEntity(
            email="expired@example.com",
            hashed_password=hash_password("password123"),
        )
        await user_repo.create(user)

        token = TokenEntity(
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        await token_repo.create(token)

        result = await token_repo.get_active_token(token.id)
        assert result is None
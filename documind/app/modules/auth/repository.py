# app/modules/auth/repository.py
# Chapter 7: repository pattern for users + tokens

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.entities import TokenEntity, UserEntity


class UserRepository:
    """All user DB operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, entity: UserEntity
    ) -> UserEntity:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get_by_id(
        self, user_id: str
    ) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(UserEntity).where(
                UserEntity.id == user_id
            )
        )
        return result.scalars().first()

    async def get_by_email(
        self, email: str
    ) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(UserEntity).where(
                UserEntity.email == email
            )
        )
        return result.scalars().first()


class TokenRepository:
    """All token DB operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, entity: TokenEntity
    ) -> TokenEntity:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get_active_token(
        self, token_id: str
    ) -> Optional[TokenEntity]:
        """
        Fetch token only if active and not expired.
        Chapter 8: database-backed revocation check.
        """
        now = datetime.now(__import__("datetime").timezone.utc)
        result = await self.session.execute(
            select(TokenEntity).where(
                TokenEntity.id == token_id,
                TokenEntity.is_active == True,       # noqa: E712
                TokenEntity.expires_at > now,
            )
        )
        return result.scalars().first()

    async def revoke(self, token_id: str) -> bool:
        """
        Mark token as inactive — logout operation.
        Chapter 8: token revocation pattern.
        """
        result = await self.session.execute(
            select(TokenEntity).where(
                TokenEntity.id == token_id
            )
        )
        token = result.scalars().first()
        if not token:
            return False
        token.is_active = False
        await self.session.flush()
        return True
# tests/integration/test_conversation_repository.py
# Chapter 11: integration tests with real SQLite DB

import pytest
from app.modules.conversations.repository import (
    ConversationRepository,
)


class TestConversationRepository:

    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session):
        """Integration — create and verify in DB."""
        repo = ConversationRepository(db_session)
        conv = await repo.create_conversation("Test Chat")

        assert conv.id is not None
        assert conv.title == "Test Chat"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, db_session):
        """Chapter 11: boundary — missing record."""
        repo = ConversationRepository(db_session)
        result = await repo.get_conversation("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_add_message_to_conversation(self, db_session):
        """Integration — message persisted correctly."""
        repo = ConversationRepository(db_session)
        conv = await repo.create_conversation("Chat")

        msg = await repo.add_message(
            conversation_id=conv.id,
            role="user",
            content="What is FastAPI?",
            rag_context_used=False,
        )

        assert msg.id is not None
        assert msg.content == "What is FastAPI?"
        assert msg.role == "user"

    @pytest.mark.asyncio
    async def test_messages_retrieved_with_conversation(
        self, db_session
    ):
        """
        Integration — messages loaded via relationship.
        Chapter 7: verify CASCADE and eager loading.
        """
        repo = ConversationRepository(db_session)
        conv = await repo.create_conversation("Chat")

        await repo.add_message(conv.id, "user", "Hello")
        await repo.add_message(conv.id, "assistant", "Hi!")

        retrieved = await repo.get_conversation(conv.id)

        assert retrieved is not None
        assert len(retrieved.messages) == 2

    @pytest.mark.asyncio
    async def test_delete_conversation_cascades_messages(
        self, db_session
    ):
        """
        Integration — CASCADE DELETE removes messages.
        Chapter 7: verify cascade constraint.
        Chapter 11: side effect verification.
        """
        from sqlalchemy import select
        from app.core.entities import MessageEntity

        repo = ConversationRepository(db_session)
        conv = await repo.create_conversation("To Delete")
        await repo.add_message(conv.id, "user", "Hello")

        deleted = await repo.delete_conversation(conv.id)
        assert deleted is True

        # Verify messages also deleted
        result = await db_session.execute(
            select(MessageEntity).where(
                MessageEntity.conversation_id == conv.id
            )
        )
        assert result.scalars().first() is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("count", [1, 5, 10])
    async def test_list_conversations_pagination(
        self, db_session, count
    ):
        """
        Chapter 11: parametrize pagination boundaries.
        """
        repo = ConversationRepository(db_session)
        for i in range(count):
            await repo.create_conversation(f"Conv {i}")

        results = await repo.list_conversations(
            skip=0, take=count
        )
        assert len(results) == count
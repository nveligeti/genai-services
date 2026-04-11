# app/modules/conversations/repository.py — replace entire file

import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.entities import ConversationEntity, MessageEntity


class ConversationRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_conversation(
        self, title: str = "New Conversation"
    ) -> ConversationEntity:
        entity = ConversationEntity(title=title)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get_conversation(
        self, conversation_id: str
    ) -> Optional[ConversationEntity]:
        result = await self.session.execute(
            select(ConversationEntity)
            .options(selectinload(ConversationEntity.messages))
            .where(ConversationEntity.id == conversation_id)
        )
        return result.scalars().first()

    # app/modules/conversations/repository.py — update list_conversations

    async def list_conversations(
        self, skip: int = 0, take: int = 20
    ) -> list[ConversationEntity]:
        result = await self.session.execute(
            select(ConversationEntity)
            .options(selectinload(ConversationEntity.messages))  # eager load
            .order_by(ConversationEntity.updated_at.desc())
            .offset(skip)
            .limit(take)
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        rag_context_used: bool = False,
        sources: Optional[list[str]] = None,
        document_id: Optional[str] = None,
        prompt_tokens: int = 0,
    ) -> MessageEntity:
        message = MessageEntity(
            conversation_id=conversation_id,
            role=role,
            content=content,
            rag_context_used=rag_context_used,
            sources=json.dumps(sources or []),
            document_id=document_id,
            prompt_tokens=prompt_tokens,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def delete_conversation(
        self, conversation_id: str
    ) -> bool:
        """
        Returns False if conversation not found.
        Returns True after successful deletion.
        """
        conv = await self.get_conversation(conversation_id)
        if not conv:
            return False          # ← must return False not raise
        await self.session.delete(conv)
        await self.session.flush()
        return True
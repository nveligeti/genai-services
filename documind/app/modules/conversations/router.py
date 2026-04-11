# app/modules/conversations/router.py — replace entire file

import json
from fastapi import APIRouter
from app.core.database import DBSessionDep
from app.exceptions import NotFoundException
from app.modules.auth.dependencies import AdminUserDep, CurrentUserDep
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationListResponse,
    ConversationOut,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation_controller(
    body: ConversationCreate,
    session: DBSessionDep,
    current_user: CurrentUserDep,        # ← protected
) -> ConversationOut:
    repo = ConversationRepository(session)
    entity = await repo.create_conversation(body.title)
    await session.commit()
    return ConversationOut(
        id=entity.id,
        title=entity.title,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        is_active=entity.is_active,
        message_count=0,
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations_controller(
    session: DBSessionDep,
    current_user: CurrentUserDep,        # ← protected
    skip: int = 0,
    take: int = 20,
) -> ConversationListResponse:
    repo = ConversationRepository(session)
    entities = await repo.list_conversations(skip, take)
    conversations = [
        ConversationOut(
            id=e.id,
            title=e.title,
            created_at=e.created_at,
            updated_at=e.updated_at,
            is_active=e.is_active,
            message_count=len(e.messages),
        )
        for e in entities
    ]
    return ConversationListResponse(
        conversations=conversations,
        total=len(conversations),
        skip=skip,
        take=take,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailOut,
)
async def get_conversation_controller(
    conversation_id: str,
    session: DBSessionDep,
    current_user: CurrentUserDep,        # ← protected
) -> ConversationDetailOut:
    repo = ConversationRepository(session)
    entity = await repo.get_conversation(conversation_id)
    if not entity:
        raise NotFoundException("Conversation", conversation_id)

    from app.modules.conversations.schemas import MessageOut
    messages = [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            rag_context_used=m.rag_context_used,
            sources=json.loads(m.sources or "[]"),
            prompt_tokens=m.prompt_tokens,
            created_at=m.created_at,
        )
        for m in entity.messages
    ]
    return ConversationDetailOut(
        id=entity.id,
        title=entity.title,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        is_active=entity.is_active,
        message_count=len(messages),
        messages=messages,
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation_controller(
    conversation_id: str,
    session: DBSessionDep,
    current_user: AdminUserDep,
) -> None:
    repo = ConversationRepository(session)
    deleted = await repo.delete_conversation(conversation_id)
    if not deleted:
        raise NotFoundException("Conversation", conversation_id)
    await session.commit()
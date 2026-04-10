# app/modules/conversations/schemas.py
# Chapter 4: Pydantic schemas for conversations API

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Annotated


class MessageOut(BaseModel):
    """Single message response."""
    model_config = {"from_attributes": True}

    id: str
    role: str
    content: str
    rag_context_used: bool
    sources: list[str] = Field(default_factory=list)
    prompt_tokens: int
    created_at: datetime


class ConversationCreate(BaseModel):
    title: Annotated[
        str,
        Field(default="New Conversation", max_length=255)
    ] = "New Conversation"


class ConversationOut(BaseModel):
    """Conversation with messages."""
    model_config = {"from_attributes": True}

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int = 0


class ConversationDetailOut(ConversationOut):
    """Conversation with full message history."""
    messages: list[MessageOut] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    conversations: list[ConversationOut]
    total: int
    skip: int
    take: int
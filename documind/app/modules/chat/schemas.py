# app/modules/chat/schemas.py
# Chapter 4: type-safe chat request/response

from enum import Enum
from pydantic import BaseModel, Field
from typing import Annotated


class MessageRole(str, Enum):
    USER      = "user"
    ASSISTANT = "assistant"
    SYSTEM    = "system"


class ChatMessage(BaseModel):
    """Single message in a conversation."""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """
    Request to the chat endpoint.
    Includes optional conversation history
    and RAG configuration.
    """
    message: Annotated[
        str,
        Field(min_length=1, max_length=4000)
    ]
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=50,          # cap history length
    )
    use_rag: bool = True        # toggle RAG retrieval
    rag_limit: Annotated[
        int,
        Field(default=3, ge=1, le=10)
    ] = 3
    rag_score_threshold: Annotated[
        float,
        Field(default=0.5, ge=0.0, le=1.0)
    ] = 0.5
    temperature: Annotated[
        float,
        Field(default=0.7, ge=0.0, le=1.0)
    ] = 0.7


class ChatResponse(BaseModel):
    """
    Non-streaming chat response.
    Used for testing and simple clients.
    """
    message: str
    rag_context_used: bool
    sources: list[str] = Field(default_factory=list)
    prompt_tokens: int = 0


class StreamEvent(BaseModel):
    """
    Single SSE event payload.
    Chapter 6: structured SSE data format.
    """
    type: str          # "token" | "done" | "error" | "rag"
    content: str = ""
    metadata: dict = Field(default_factory=dict)
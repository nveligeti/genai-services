# app/core/entities.py — replace entire file

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentEntity(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True,
    )
    filename: Mapped[str] = mapped_column(String(255))
    filepath: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(
        String(20), index=True   # index=True handles this
    )
    size_bytes: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(100))
    chunk_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4().hex)
        kwargs.setdefault("status", "pending")
        kwargs.setdefault("uploaded_at", utcnow())
        super().__init__(**kwargs)

    messages: Mapped[list["MessageEntity"]] = relationship(
        "MessageEntity",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    # NO __table_args__ — removes duplicate index creation


class ConversationEntity(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    is_active: Mapped[bool] = mapped_column(Boolean)

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4().hex)
        kwargs.setdefault("title", "New Conversation")
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("created_at", utcnow())
        kwargs.setdefault("updated_at", utcnow())
        super().__init__(**kwargs)

    messages: Mapped[list["MessageEntity"]] = relationship(
        "MessageEntity",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MessageEntity.created_at",
    )


class MessageEntity(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True,
    )
    conversation_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    rag_context_used: Mapped[bool] = mapped_column(Boolean)
    sources: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4().hex)
        kwargs.setdefault("rag_context_used", False)
        kwargs.setdefault("prompt_tokens", 0)
        kwargs.setdefault("created_at", utcnow())
        super().__init__(**kwargs)

    conversation: Mapped["ConversationEntity"] = relationship(
        "ConversationEntity", back_populates="messages"
    )
    document: Mapped[Optional["DocumentEntity"]] = relationship(
        "DocumentEntity", back_populates="messages"
    )
    # NO __table_args__ — removes duplicate index creation
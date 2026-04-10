# app/modules/auth/entities.py
# Chapter 8: User and Token ORM models

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
    )
    role: Mapped[str] = mapped_column(
        String(20),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    tokens: Mapped[list["TokenEntity"]] = relationship(
        "TokenEntity",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4().hex)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("role", "USER")
        kwargs.setdefault("created_at", utcnow())
        kwargs.setdefault("updated_at", utcnow())
        super().__init__(**kwargs)


class TokenEntity(Base):
    __tablename__ = "tokens"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    user: Mapped["UserEntity"] = relationship(
        "UserEntity", back_populates="tokens"
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4().hex)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("created_at", utcnow())
        super().__init__(**kwargs)
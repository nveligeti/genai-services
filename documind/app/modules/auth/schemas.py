# app/modules/auth/schemas.py
# Chapter 4: type-safe auth request/response

from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: Annotated[
        str,
        Field(min_length=8, max_length=100),
    ]
    role: str = "USER"


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response after successful login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600   # seconds


class UserOut(BaseModel):
    """Safe user response — never exposes password."""
    model_config = {"from_attributes": True}

    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class AuthenticatedUser(BaseModel):
    """
    Injected into route handlers via dependency.
    Chapter 8: carries user context through request.
    """
    user_id: str
    email: str
    role: str
    token_id: str
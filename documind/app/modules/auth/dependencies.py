# app/modules/auth/dependencies.py
# Chapter 8: FastAPI dependency guards

from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.exceptions import ForbiddenException
from app.modules.auth.schemas import AuthenticatedUser
from app.modules.auth.service import AuthService

# FastAPI's built-in Bearer token extractor
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthenticatedUser:
    """
    Extract and validate Bearer token.
    Chapter 8: injected into every protected route.

    Returns AuthenticatedUser for use in route handlers.
    Raises UnauthorizedException (401) if invalid.
    """
    from app.exceptions import UnauthorizedException

    if not credentials:
        raise UnauthorizedException(
            "Authorization header missing"
        )

    service = AuthService(session)
    return await service.get_authenticated_user(
        credentials.credentials
    )


async def get_admin_user(
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
) -> AuthenticatedUser:
    """
    RBAC guard — admin only.
    Chapter 8: 403 Forbidden for non-admin users.
    Chapter 11: separate from 401 — user IS authenticated
                but NOT authorized.
    """
    if current_user.role != "ADMIN":
        raise ForbiddenException(
            "Admin access required"
        )
    return current_user


# Annotated types for clean route injection
CurrentUserDep = Annotated[
    AuthenticatedUser,
    Depends(get_current_user),
]

AdminUserDep = Annotated[
    AuthenticatedUser,
    Depends(get_admin_user),
]
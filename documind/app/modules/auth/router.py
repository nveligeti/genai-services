# app/modules/auth/router.py
# Chapter 8: auth endpoints

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.modules.auth.dependencies import CurrentUserDep
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.modules.auth.service import AuthService
from typing import Annotated

router = APIRouter(prefix="/auth", tags=["Auth"])

DBSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_auth_service(session: DBSession) -> AuthService:
    return AuthService(session)


AuthServiceDep = Annotated[
    AuthService, Depends(get_auth_service)
]


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
    summary="Register a new user",
)
async def register_controller(
    body: RegisterRequest,
    service: AuthServiceDep,
) -> UserOut:
    """
    Public endpoint — no auth required.
    Chapter 8: returns UserOut (never exposes password).
    """
    return await service.register(body)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT token",
)
async def login_controller(
    body: LoginRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    """
    Public endpoint — no auth required.
    Chapter 8: returns bearer token on success.
    """
    return await service.login(body)


@router.post(
    "/logout",
    status_code=204,
    summary="Revoke current token",
)
async def logout_controller(
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> None:
    """
    Protected endpoint — requires valid token.
    Chapter 8: revokes token so it can't be reused.
    """
    await service.logout(current_user)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
)
async def me_controller(
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> UserOut:
    """Fetch profile of currently authenticated user."""
    from app.modules.auth.repository import UserRepository
    from app.core.database import get_db_session
    user_repo = UserRepository(service.session)
    user = await user_repo.get_by_id(current_user.user_id)
    return UserOut.model_validate(user)
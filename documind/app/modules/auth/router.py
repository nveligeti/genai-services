# app/modules/auth/router.py — replace entire file

from typing import Annotated
from fastapi import APIRouter, Depends, Request
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
)
async def register_controller(
    request: Request,
    body: RegisterRequest,
    service: AuthServiceDep,
) -> UserOut:
    return await service.register(body)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login_controller(
    request: Request,
    body: LoginRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.login(body)


@router.post("/logout", status_code=204)
async def logout_controller(
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> None:
    await service.logout(current_user)


@router.get("/me", response_model=UserOut)
async def me_controller(
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> UserOut:
    from app.modules.auth.repository import UserRepository
    user_repo = UserRepository(service.session)
    user = await user_repo.get_by_id(current_user.user_id)
    return UserOut.model_validate(user)
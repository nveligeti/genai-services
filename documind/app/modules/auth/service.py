# app/modules/auth/service.py
# Chapter 8: AuthService orchestrates register/login/logout

import uuid
from datetime import timedelta
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)
from app.exceptions import (
    ForbiddenException,
    UnauthorizedException,
    ValidationException,
)
from app.modules.auth.entities import TokenEntity, UserEntity
from app.modules.auth.repository import (
    TokenRepository,
    UserRepository,
)
from app.modules.auth.schemas import (
    AuthenticatedUser,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.modules.auth.entities import utcnow
from datetime import timedelta


class AuthService:
    """
    Orchestrates all authentication flows.
    Chapter 8: register → login → protect → logout.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = TokenRepository(session)

    async def register(
        self, request: RegisterRequest
    ) -> UserOut:
        """
        Register a new user.
        Chapter 8: hash password before storing — NEVER plain text.
        """
        # Check duplicate email
        existing = await self.user_repo.get_by_email(
            request.email
        )
        if existing:
            raise ValidationException(
                f"Email '{request.email}' already registered"
            )

        # Hash password with bcrypt + auto salt
        hashed = hash_password(request.password)

        entity = UserEntity(
            email=request.email,
            hashed_password=hashed,
            role=request.role.upper(),
        )

        created = await self.user_repo.create(entity)
        await self.session.commit()

        logger.info(f"User registered | email={request.email}")

        return UserOut.model_validate(created)

    async def login(
        self, request: LoginRequest
    ) -> TokenResponse:
        """
        Authenticate user and issue JWT.
        Chapter 8: verify → issue → store token.
        """
        # Fetch user
        user = await self.user_repo.get_by_email(request.email)

        # Use same error for missing user and wrong password
        # Chapter 8: prevents user enumeration attacks
        if not user or not verify_password(
            request.password, user.hashed_password
        ):
            raise UnauthorizedException(
                "Invalid email or password"
            )

        if not user.is_active:
            raise ForbiddenException("Account is deactivated")

        # Create token record first to get token_id
        token_id = uuid.uuid4().hex
        expires_at = utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

        token_entity = TokenEntity(
            id=token_id,
            user_id=user.id,
            expires_at=expires_at,
        )
        await self.token_repo.create(token_entity)

        # Sign JWT with token_id for revocation support
        access_token = create_access_token(
            user_id=user.id,
            token_id=token_id,
            role=user.role,
        )

        await self.session.commit()

        logger.info(f"User logged in | email={request.email}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(
        self, authenticated_user: AuthenticatedUser
    ) -> None:
        """
        Revoke token — future requests with same token fail.
        Chapter 8: database-backed token revocation.
        """
        revoked = await self.token_repo.revoke(
            authenticated_user.token_id
        )
        if revoked:
            await self.session.commit()
            logger.info(
                f"Token revoked | "
                f"user={authenticated_user.email}"
            )

    async def get_authenticated_user(
        self, token: str
    ) -> AuthenticatedUser:
        """
        Validate JWT + verify token is active in DB.
        Chapter 8: two-layer validation.
        """
        from app.core.security import decode_access_token

        # Layer 1 — verify JWT signature and expiry
        claims = decode_access_token(token)

        # Layer 2 — verify token not revoked in DB
        token_entity = await self.token_repo.get_active_token(
            claims["token_id"]
        )
        if not token_entity:
            raise UnauthorizedException(
                "Token has been revoked or expired"
            )

        # Fetch user
        user = await self.user_repo.get_by_id(
            claims["user_id"]
        )
        if not user or not user.is_active:
            raise UnauthorizedException(
                "User not found or deactivated"
            )

        return AuthenticatedUser(
            user_id=user.id,
            email=user.email,
            role=user.role,
            token_id=claims["token_id"],
        )
# app/core/security.py
# Chapter 8: JWT encoding/decoding + bcrypt hashing
# Uses bcrypt directly — avoids passlib 72-byte restriction

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.exceptions import UnauthorizedException

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(plain_password: str) -> str:
    """
    Hash password with bcrypt + auto-generated salt.
    Chapter 8: same password → different hash every time.
    bcrypt directly — no passlib 72-byte restriction.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify plain password against stored bcrypt hash.
    Chapter 8: constant-time comparison prevents timing attacks.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(
    user_id: str,
    token_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create signed JWT token.
    Chapter 8: header.payload.signature format.
    """
    from app.settings import get_settings
    settings = get_settings()

    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub":  user_id,
        "jti":  token_id,
        "role": role,
        "exp":  expire,
        "iat":  now,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    Chapter 8: raises UnauthorizedException on any failure.
    """
    from app.settings import get_settings
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
        user_id: str = payload.get("sub")
        token_id: str = payload.get("jti")
        role: str = payload.get("role")

        if not user_id or not token_id:
            raise UnauthorizedException(
                "Token missing required claims"
            )

        return {
            "user_id":  user_id,
            "token_id": token_id,
            "role":     role,
        }

    except JWTError as e:
        raise UnauthorizedException(
            f"Invalid or expired token: {e}"
        )
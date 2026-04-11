# app/core/rate_limiter.py — replace entire file

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse


def get_rate_limit_key(request: Request) -> str:
    """Rate limit key — user-based or IP-based."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.core.security import decode_access_token
            token = auth_header.split(" ")[1]
            claims = decode_access_token(token)
            return f"user:{claims['user_id']}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["100/minute"],
)


def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> Response:
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                f"Rate limit exceeded. "
                f"Try again in {retry_after} seconds."
            )
        },
        headers={"Retry-After": str(retry_after)},
    )
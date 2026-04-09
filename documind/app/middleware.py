# app/middleware.py
# Chapter 3: Request logging and tracing middleware
# Chapter 6: CORS middleware

import time
import uuid
from typing import Awaitable, Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


def register_middleware(app: FastAPI) -> None:
    """
    Register all middleware.
    IMPORTANT: Do NOT call get_settings() here at function scope.
    Call it inside the request handler so the test override works.
    """

    # Import inside function to avoid module-level cache population
    from app.settings import get_settings

    @app.middleware("http")
    async def logging_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = uuid.uuid4().hex
        start_time = time.perf_counter()
        request.state.request_id = request_id

        response = await call_next(request)

        duration = round(time.perf_counter() - start_time, 4)

        logger.info(
            f"request_id={request_id} "
            f"method={request.method} "
            f"path={request.url.path} "
            f"status={response.status_code} "
            f"duration={duration}s"
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(duration)

        return response

    # CORS — read settings per request via dependency, not at startup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # tightened in Phase 8 via settings
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
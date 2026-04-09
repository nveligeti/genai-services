# app/exceptions.py
# Chapter 2: Global exception hierarchy and handlers

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger


class DocuMindException(Exception):
    """Base exception for all DocuMind errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(DocuMindException):
    def __init__(self, resource: str, uid: str | int) -> None:
        super().__init__(
            message=f"{resource} with id '{uid}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationException(DocuMindException):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class UnauthorizedException(DocuMindException):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(DocuMindException):
    def __init__(self, message: str = "Not permitted") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers."""

    @app.exception_handler(DocuMindException)
    async def documind_exception_handler(
        request: Request, exc: DocuMindException
    ) -> JSONResponse:
        logger.warning(
            f"DocuMindException | {exc.status_code} | "
            f"{request.method} {request.url.path} | {exc.message}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            f"Unhandled exception | "
            f"{request.method} {request.url.path} | {exc}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred"},
        )

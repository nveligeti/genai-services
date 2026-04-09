#!/bin/bash

# =============================================================================
# DocuMind — Project Structure Setup Script
# Based on: Building Generative AI Services with FastAPI
# Phase 1: Project Scaffolding
# =============================================================================

set -e  # Exit immediately on error

# --- Colors for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Helpers ---
print_header() {
    echo -e "\n${BOLD}${BLUE}============================================${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}============================================${NC}\n"
}

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

make_file() {
    local filepath="$1"
    local dir
    dir=$(dirname "$filepath")
    mkdir -p "$dir"
    touch "$filepath"
    echo -e "  ${GREEN}+${NC} $filepath"
}

# =============================================================================
# ENTRY POINT
# =============================================================================

print_header "DocuMind — Project Setup"

# --- Get project name ---
PROJECT_NAME="${1:-documind}"
echo -e "${BOLD}Project name:${NC} ${CYAN}$PROJECT_NAME${NC}"

# --- Check if directory already exists ---
if [ -d "$PROJECT_NAME" ]; then
    print_warning "Directory '$PROJECT_NAME' already exists."
    read -p "  Overwrite? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        print_error "Aborted."
        exit 1
    fi
    rm -rf "$PROJECT_NAME"
    echo ""
fi

mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"
print_success "Created project directory: $PROJECT_NAME"

# =============================================================================
# STEP 1 — DIRECTORY STRUCTURE
# =============================================================================

print_header "Step 1: Creating Directory Structure"

print_step "Creating application directories..."
mkdir -p app/modules/health
mkdir -p app/modules/documents
mkdir -p app/modules/rag
mkdir -p app/modules/chat
mkdir -p app/modules/conversations
mkdir -p app/modules/auth
mkdir -p app/core
mkdir -p app/providers

print_step "Creating test directories..."
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/e2e

print_step "Creating supporting directories..."
mkdir -p alembic/versions

print_success "Directory structure created"

# =============================================================================
# STEP 2 — __init__.py FILES
# =============================================================================

print_header "Step 2: Creating __init__.py Files"

INIT_FILES=(
    "app/__init__.py"
    "app/modules/__init__.py"
    "app/modules/health/__init__.py"
    "app/modules/documents/__init__.py"
    "app/modules/rag/__init__.py"
    "app/modules/chat/__init__.py"
    "app/modules/conversations/__init__.py"
    "app/modules/auth/__init__.py"
    "app/core/__init__.py"
    "app/providers/__init__.py"
    "tests/__init__.py"
    "tests/unit/__init__.py"
    "tests/integration/__init__.py"
    "tests/e2e/__init__.py"
)

for f in "${INIT_FILES[@]}"; do
    make_file "$f"
done

print_success "__init__.py files created"

# =============================================================================
# STEP 3 — PLACEHOLDER FILES (to be filled in subsequent steps)
# =============================================================================

print_header "Step 3: Creating Application Files"

# --- Core app files ---
print_step "Creating core application files..."
make_file "app/main.py"
make_file "app/settings.py"
make_file "app/exceptions.py"
make_file "app/middleware.py"

# --- Module files ---
print_step "Creating module files..."
make_file "app/modules/health/router.py"

# Phase 2 placeholders
make_file "app/modules/documents/router.py"
make_file "app/modules/documents/schemas.py"
make_file "app/modules/documents/service.py"

# Phase 3 placeholders
make_file "app/modules/rag/pipeline.py"
make_file "app/modules/rag/repository.py"
make_file "app/modules/rag/schemas.py"

# Phase 4 placeholders
make_file "app/modules/chat/router.py"
make_file "app/modules/chat/schemas.py"
make_file "app/modules/chat/service.py"

# Phase 5 placeholders
make_file "app/modules/conversations/router.py"
make_file "app/modules/conversations/schemas.py"
make_file "app/modules/conversations/service.py"
make_file "app/modules/conversations/repository.py"
make_file "app/modules/conversations/entities.py"

# Phase 6 placeholders
make_file "app/modules/auth/router.py"
make_file "app/modules/auth/schemas.py"
make_file "app/modules/auth/service.py"
make_file "app/modules/auth/dependencies.py"
make_file "app/modules/auth/entities.py"

# --- Core files ---
print_step "Creating core infrastructure files..."
make_file "app/core/database.py"     # Phase 5
make_file "app/core/security.py"     # Phase 6

# --- Provider files ---
print_step "Creating provider files..."
make_file "app/providers/llm.py"     # Phase 2

# --- Test files ---
print_step "Creating test files..."
make_file "tests/conftest.py"
make_file "tests/unit/test_settings.py"
make_file "tests/e2e/test_health.py"

print_success "Application files created"

# =============================================================================
# STEP 4 — WRITE REQUIREMENTS FILES
# =============================================================================

print_header "Step 4: Writing Requirements Files"

print_step "Writing requirements.txt..."
cat > requirements.txt << 'EOF'
# Web framework
fastapi[standard]==0.115.0
uvicorn[standard]==0.30.6

# Data validation
pydantic==2.8.2
pydantic-settings==2.4.0

# Logging
loguru==0.7.2

# File handling
python-multipart==0.0.9

# HTTP client
httpx==0.27.2

# Phase 2: RAG + vector DB
# qdrant-client==1.11.1
# pypdf==5.0.1
# aiofiles==24.1.0
# transformers==4.44.2
# torch==2.4.1

# Phase 5: Database
# sqlalchemy[asyncio]==2.0.35
# alembic==1.13.3
# psycopg[binary]==3.2.3

# Phase 7: Rate limiting + Redis
# slowapi==0.1.9
# coredis==4.4.2

# Phase 8: Caching
# fastapi-cache2[redis]==0.2.2
EOF
echo -e "  ${GREEN}+${NC} requirements.txt"

print_step "Writing requirements-dev.txt..."
cat > requirements-dev.txt << 'EOF'
-r requirements.txt

# Testing
pytest==8.3.2
pytest-asyncio==0.23.8
pytest-mock==3.14.0
coverage==7.6.1

# Phase 5: Async test DB
# aiosqlite==0.20.0

# Code quality
mypy==1.11.2
ruff==0.6.5
EOF
echo -e "  ${GREEN}+${NC} requirements-dev.txt"

print_success "Requirements files created"

# =============================================================================
# STEP 5 — WRITE SETTINGS
# =============================================================================

print_header "Step 5: Writing Settings (Chapter 4 — Pydantic BaseSettings)"

cat > app/settings.py << 'EOF'
# app/settings.py
# Chapter 4: Pydantic BaseSettings for type-safe configuration

from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "DocuMind"
    app_version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Security (Phase 6)
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-min-32-chars",
        min_length=32,
    )

    # LLM (Phase 2)
    llm_provider: Literal["mock", "openai", "anthropic"] = "mock"
    llm_model: str = "mock-gpt"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    llm_max_tokens: int = Field(default=1024, ge=1, le=8192)

    # Database (Phase 5)
    database_url: str = (
        "postgresql+psycopg://user:password@localhost:5432/documind"
    )

    # Vector Database (Phase 3)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # Redis (Phase 7)
    redis_url: str = "redis://localhost:6379"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    return Settings()
EOF
echo -e "  ${GREEN}+${NC} app/settings.py"
print_success "Settings written"

# =============================================================================
# STEP 6 — WRITE EXCEPTIONS
# =============================================================================

print_header "Step 6: Writing Exception Handlers (Chapter 2)"

cat > app/exceptions.py << 'EOF'
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
EOF
echo -e "  ${GREEN}+${NC} app/exceptions.py"
print_success "Exceptions written"

# =============================================================================
# STEP 7 — WRITE MIDDLEWARE
# =============================================================================

print_header "Step 7: Writing Middleware (Chapter 3 — Request Logging)"

cat > app/middleware.py << 'EOF'
# app/middleware.py
# Chapter 3: Request logging and tracing middleware
# Chapter 6: CORS middleware

import time
import uuid
from typing import Awaitable, Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.settings import get_settings


def register_middleware(app: FastAPI) -> None:
    """Register all middleware in correct order.

    Note: Middleware is applied in REVERSE order of registration.
    Last registered = outermost layer (runs first).
    """
    settings = get_settings()

    # CORS — must be registered before logging middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging and distributed tracing
    @app.middleware("http")
    async def logging_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = uuid.uuid4().hex
        start_time = time.perf_counter()

        # Attach request ID to request state for use in route handlers
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

        # Attach tracing headers to every response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(duration)

        return response
EOF
echo -e "  ${GREEN}+${NC} app/middleware.py"
print_success "Middleware written"

# =============================================================================
# STEP 8 — WRITE HEALTH ROUTER
# =============================================================================

print_header "Step 8: Writing Health Router (Chapter 2)"

cat > app/modules/health/router.py << 'EOF'
# app/modules/health/router.py
# Chapter 2: Modular router pattern
# Chapter 4: Typed response with Pydantic BaseModel

from fastapi import APIRouter
from pydantic import BaseModel
from app.settings import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Never rate-limited (Chapter 9).
    Used by Docker health checks (Chapter 12).
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )
EOF
echo -e "  ${GREEN}+${NC} app/modules/health/router.py"
print_success "Health router written"

# =============================================================================
# STEP 9 — WRITE MAIN APPLICATION
# =============================================================================

print_header "Step 9: Writing Main Application (Chapter 2 — App Factory)"

cat > app/main.py << 'EOF'
# app/main.py
# Chapter 2: Application factory pattern + onion architecture
# Chapter 5: Lifespan for async startup/shutdown

from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from loguru import logger
from app.settings import get_settings
from app.exceptions import register_exception_handlers
from app.middleware import register_middleware
from app.modules.health.router import router as health_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan context manager.
    Startup code runs before yield.
    Shutdown code runs after yield.

    Chapter 5: Used to initialize async resources.
    """
    settings = get_settings()
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"[{settings.environment}]"
    )

    # ── Phase 2: LLM client initialization ──────────────────────
    # from app.providers.llm import get_llm_client
    # await get_llm_client().initialize()

    # ── Phase 3: Qdrant collection setup ────────────────────────
    # from app.modules.rag.repository import VectorRepository
    # await VectorRepository().ensure_collection()

    # ── Phase 5: Database engine initialization ─────────────────
    # from app.core.database import init_db
    # await init_db()

    yield  # ── Application is running ───────────────────────────

    logger.info(f"Shutting down {settings.app_name}")

    # ── Phase 5: Database engine disposal ───────────────────────
    # from app.core.database import dispose_db
    # await dispose_db()


def create_app() -> FastAPI:
    """
    Application factory.
    Returns a fully configured FastAPI instance.
    Used in tests to create isolated app instances.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="RAG-powered document intelligence service",
        # Disable docs in production (Chapter 8: security)
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Register cross-cutting concerns
    register_middleware(app)
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────
    app.include_router(health_router)

    # Phase 2: Document upload
    # from app.modules.documents.router import router as documents_router
    # app.include_router(documents_router)

    # Phase 3: RAG query
    # from app.modules.rag.router import router as rag_router
    # app.include_router(rag_router)

    # Phase 4: Chat streaming
    # from app.modules.chat.router import router as chat_router
    # app.include_router(chat_router)

    # Phase 5: Conversation history
    # from app.modules.conversations.router import router as conversations_router
    # app.include_router(conversations_router)

    # Phase 6: Authentication
    # from app.modules.auth.router import router as auth_router
    # app.include_router(auth_router)

    return app


# Application instance for uvicorn
app = create_app()
EOF
echo -e "  ${GREEN}+${NC} app/main.py"
print_success "Main application written"

# =============================================================================
# STEP 10 — WRITE ENVIRONMENT FILES
# =============================================================================

print_header "Step 10: Writing Environment Files"

cat > .env.example << 'EOF'
# =============================================================================
# DocuMind — Environment Configuration
# Copy this file to .env and update values
# NEVER commit .env to version control
# =============================================================================

# Application
APP_NAME=DocuMind
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Security (Phase 6) — CHANGE THIS IN PRODUCTION
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars

# LLM Provider (Phase 2)
LLM_PROVIDER=mock
LLM_MODEL=mock-gpt
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024

# Uncomment for real providers:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...

# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Database (Phase 5)
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/documind

# Vector Database (Phase 3)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis (Phase 7)
REDIS_URL=redis://localhost:6379
EOF
echo -e "  ${GREEN}+${NC} .env.example"

cp .env.example .env
echo -e "  ${GREEN}+${NC} .env (copied from .env.example)"
print_success "Environment files created"

# =============================================================================
# STEP 11 — WRITE TEST FILES
# =============================================================================

print_header "Step 11: Writing Test Files (Chapter 11)"

cat > tests/conftest.py << 'EOF'
# tests/conftest.py
# Chapter 11: Session-scoped fixtures for test isolation

import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.settings import Settings, get_settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Override settings for the entire test session.
    Chapter 4: Pydantic Settings with environment override.
    Chapter 11: Isolated test environment.
    """
    return Settings(
        environment="testing",
        debug=True,
        llm_provider="mock",
        secret_key="test-secret-key-exactly-32-chars-long",
        database_url="sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture(scope="session")
def app(test_settings: Settings):
    """
    Create test application with dependency overrides.
    Chapter 11: Application fixture for testing.
    """
    def override_settings() -> Settings:
        return test_settings

    application = create_app()
    application.dependency_overrides[get_settings] = override_settings
    return application


@pytest.fixture(scope="session")
def client(app) -> TestClient:
    """
    Synchronous test client for non-async tests.
    Chapter 11: Shared session-scoped client fixture.
    """
    with TestClient(app) as c:
        yield c
EOF
echo -e "  ${GREEN}+${NC} tests/conftest.py"

cat > tests/unit/test_settings.py << 'EOF'
# tests/unit/test_settings.py
# Chapter 11: Unit tests for Pydantic settings validation
# Chapter 4: Type safety verification

import pytest
from pydantic import ValidationError
from app.settings import Settings


class TestSettings:
    """
    Unit tests for Settings validation.

    Chapter 11 patterns used:
    - Invalid data testing (boundary violations)
    - Valid data testing (happy path)
    - Property-based assertions
    """

    def test_default_settings_are_valid(self) -> None:
        """Valid settings must initialize without errors."""
        settings = Settings(
            secret_key="a-valid-secret-key-that-is-32-chars-long"
        )
        assert settings.app_name == "DocuMind"
        assert settings.environment == "development"
        assert settings.llm_provider == "mock"

    def test_secret_key_too_short_raises_validation_error(self) -> None:
        """
        Chapter 11: boundary test — below minimum length.
        Chapter 4: Field(min_length=32) enforced at runtime.
        """
        with pytest.raises(ValidationError) as exc_info:
            Settings(secret_key="too-short")
        assert "min_length" in str(exc_info.value).lower() \
            or "secret_key" in str(exc_info.value).lower()

    def test_llm_temperature_too_high_raises_error(self) -> None:
        """
        Chapter 11: boundary test — above maximum value.
        Chapter 4: Field(le=1.0) enforced.
        """
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a-valid-secret-key-that-is-32-chars-long",
                llm_temperature=1.5,
            )

    def test_llm_temperature_too_low_raises_error(self) -> None:
        """
        Chapter 11: boundary test — below minimum value.
        Chapter 4: Field(ge=0.0) enforced.
        """
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a-valid-secret-key-that-is-32-chars-long",
                llm_temperature=-0.1,
            )

    def test_llm_temperature_at_boundary_values_passes(self) -> None:
        """
        Chapter 11: boundary test — exactly at limits must pass.
        """
        for temp in [0.0, 1.0]:
            settings = Settings(
                secret_key="a-valid-secret-key-that-is-32-chars-long",
                llm_temperature=temp,
            )
            assert settings.llm_temperature == temp

    def test_invalid_environment_raises_error(self) -> None:
        """
        Chapter 11: invalid data test — unsupported environment.
        Chapter 4: Literal type enforced.
        """
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a-valid-secret-key-that-is-32-chars-long",
                environment="staging",  # not in Literal
            )

    def test_is_production_true_when_environment_is_production(self) -> None:
        """Chapter 11: property-based assertion."""
        settings = Settings(
            secret_key="a-valid-secret-key-that-is-32-chars-long",
            environment="production",
        )
        assert settings.is_production is True
        assert settings.is_testing is False

    def test_is_testing_true_when_environment_is_testing(self) -> None:
        """Chapter 11: property-based assertion."""
        settings = Settings(
            secret_key="a-valid-secret-key-that-is-32-chars-long",
            environment="testing",
        )
        assert settings.is_testing is True
        assert settings.is_production is False

    def test_is_production_false_in_development(self) -> None:
        """Chapter 11: valid data — default environment check."""
        settings = Settings(
            secret_key="a-valid-secret-key-that-is-32-chars-long",
        )
        assert settings.is_production is False
        assert settings.is_testing is False
EOF
echo -e "  ${GREEN}+${NC} tests/unit/test_settings.py"

cat > tests/e2e/test_health.py << 'EOF'
# tests/e2e/test_health.py
# Chapter 11: Vertical E2E tests for the health endpoint
# Tests behavior (contract) not implementation

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """
    E2E tests for /health endpoint.

    Chapter 11 patterns used:
    - Contract-based assertions (not exact values)
    - Middleware side effect verification
    - Nonbrittle test design
    """

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health endpoint must always be reachable."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_is_json(self, client: TestClient) -> None:
        """Response must be valid JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        assert response.json() is not None

    def test_health_response_contract(self, client: TestClient) -> None:
        """
        Response must contain all required fields.
        Chapter 11: contract assertion — not exact values.
        """
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "environment" in data

    def test_health_status_is_healthy(self, client: TestClient) -> None:
        """Status field must always be 'healthy'."""
        response = client.get("/health")
        assert response.json()["status"] == "healthy"

    def test_health_environment_reflects_test_override(
        self, client: TestClient
    ) -> None:
        """
        Environment must reflect test settings dependency override.
        Chapter 11: verifies DI override works correctly.
        """
        response = client.get("/health")
        assert response.json()["environment"] == "testing"

    def test_health_includes_request_id_header(
        self, client: TestClient
    ) -> None:
        """
        Middleware must attach X-Request-ID to every response.
        Chapter 11: verify middleware side effect.
        """
        response = client.get("/health")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) == 32  # hex UUID

    def test_health_includes_response_time_header(
        self, client: TestClient
    ) -> None:
        """
        Middleware must attach X-Response-Time to every response.
        Chapter 11: verify middleware side effect.
        """
        response = client.get("/health")
        assert "x-response-time" in response.headers
        duration = float(response.headers["x-response-time"])
        assert duration >= 0

    def test_health_request_id_is_unique_per_request(
        self, client: TestClient
    ) -> None:
        """
        Each request must receive a unique request ID.
        Chapter 11: invariance test — IDs must never repeat.
        """
        response1 = client.get("/health")
        response2 = client.get("/health")

        id1 = response1.headers["x-request-id"]
        id2 = response2.headers["x-request-id"]

        assert id1 != id2
EOF
echo -e "  ${GREEN}+${NC} tests/e2e/test_health.py"
print_success "Test files written"

# =============================================================================
# STEP 12 — WRITE PYTEST CONFIG
# =============================================================================

print_header "Step 12: Writing Pytest Configuration"

cat > pytest.ini << 'EOF'
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --tb=short
    --strict-markers
    -v
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (requires running services)
    e2e: End-to-end tests (full application stack)
    slow: Slow running tests
EOF
echo -e "  ${GREEN}+${NC} pytest.ini"
print_success "Pytest config written"

# =============================================================================
# STEP 13 — WRITE .gitignore
# =============================================================================

print_header "Step 13: Writing .gitignore"

cat > .gitignore << 'EOF'
# Environment
.env
*.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# IDEs
.idea/
.vscode/
*.swp

# Docker
*.log

# OS
.DS_Store
Thumbs.db

# Data
uploads/
qdrant_storage/
dbstorage/
EOF
echo -e "  ${GREEN}+${NC} .gitignore"
print_success ".gitignore written"

# =============================================================================
# STEP 14 — PRINT FINAL TREE
# =============================================================================

print_header "Phase 1 Complete — Project Structure"

if command -v tree &> /dev/null; then
    tree -a -I ".git|__pycache__|*.pyc|.DS_Store" .
else
    find . -not -path "./.git/*" -not -name "*.pyc" \
           -not -name "__pycache__" | sort | \
    awk '{
        n = split($0, a, "/")
        indent = ""
        for (i = 2; i < n; i++) indent = indent "│   "
        if (n > 1) printf "%s├── %s\n", indent, a[n]
        else print a[n]
    }'
fi

# =============================================================================
# STEP 15 — NEXT STEPS
# =============================================================================

print_header "Next Steps"

echo -e "${BOLD}1. Install dependencies:${NC}"
echo -e "   ${CYAN}cd $PROJECT_NAME${NC}"
echo -e "   ${CYAN}python -m venv .venv${NC}"
echo -e "   ${CYAN}source .venv/bin/activate${NC}  ${YELLOW}# Windows: .venv\\Scripts\\activate${NC}"
echo -e "   ${CYAN}pip install -r requirements-dev.txt${NC}\n"

echo -e "${BOLD}2. Run the server:${NC}"
echo -e "   ${CYAN}uvicorn app.main:app --reload${NC}"
echo -e "   ${YELLOW}→ Visit: http://localhost:8000/docs${NC}\n"

echo -e "${BOLD}3. Run the tests:${NC}"
echo -e "   ${CYAN}pytest tests/ -v${NC}"
echo -e "   ${YELLOW}→ Expected: 11 passed${NC}\n"

echo -e "${BOLD}4. Check health endpoint:${NC}"
echo -e "   ${CYAN}curl http://localhost:8000/health${NC}\n"

echo -e "${GREEN}${BOLD}✅ Phase 1 scaffolding complete!${NC}"
echo -e "${YELLOW}   Ready for Phase 2: Mock LLM + Document Upload${NC}\n"
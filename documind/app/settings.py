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

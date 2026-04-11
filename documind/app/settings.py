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
    # RAG (Phase 3)
    embedding_model: str = "mock"
    embedding_dimension: int = 384
    rag_collection_name: str = "documind"
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_retrieval_limit: int = 3
    rag_score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    # Redis (Phase 7)
    redis_url: str = "redis://localhost:6379"

    # app/settings.py — add inside Settings class

    # Cache settings (Phase 8)
    cache_enabled: bool = True
    keyword_cache_ttl: int = 3600
    semantic_cache_ttl: int = 7200
    semantic_cache_threshold: float = Field(
        default=0.92, ge=0.0, le=1.0
    )
    semantic_cache_max_entries: int = 1000
    cache_collection_name: str = "documind_cache"

    # Prompt settings (Phase 8)
    max_context_tokens: int = 3000
    max_response_tokens: int = 500

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    return Settings()



# app/modules/cache/schemas.py
# Chapter 10: type-safe cache entry models

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Annotated


class CacheEntry(BaseModel):
    """A single cached query-response pair."""
    query: str
    normalized_query: str
    response: str
    sources: list[str] = Field(default_factory=list)
    rag_context_used: bool = False
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    hit_count: int = 0
    cache_type: str = "keyword"   # "keyword" | "semantic"


class CacheHit(BaseModel):
    """Result of a successful cache lookup."""
    entry: CacheEntry
    similarity_score: float = 1.0   # 1.0 for keyword hits
    cache_type: str = "keyword"


class CacheStats(BaseModel):
    """Aggregate cache statistics."""
    keyword_hits: int = 0
    semantic_hits: int = 0
    misses: int = 0
    total_requests: int = 0

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        hits = self.keyword_hits + self.semantic_hits
        return round(hits / self.total_requests, 4)

    
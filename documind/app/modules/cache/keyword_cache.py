# app/modules/cache/keyword_cache.py
# Chapter 10: exact-match Redis cache

import hashlib
import json
from datetime import datetime
from typing import Optional
from loguru import logger
from app.modules.cache.schemas import CacheEntry, CacheHit


class KeywordCache:
    """
    Exact-match cache using Redis.
    Chapter 10: fastest cache layer — O(1) lookup.

    Key strategy:
      normalize query → sha256 hash → Redis GET/SET
    """

    def __init__(
        self,
        redis_client,
        ttl: int = 3600,
    ) -> None:
        self.redis = redis_client
        self.ttl = ttl

    def _make_key(self, query: str) -> str:
        """
        Normalize query and hash it.
        Chapter 10: case-insensitive, whitespace-normalized.
        """
        normalized = " ".join(query.lower().strip().split())
        hashed = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()
        return f"keyword:{hashed}"

    def _normalize(self, query: str) -> str:
        return " ".join(query.lower().strip().split())

    async def get(self, query: str) -> Optional[CacheHit]:
        """
        Look up query in keyword cache.
        Returns CacheHit on hit, None on miss.
        """
        try:
            key = self._make_key(query)
            raw = await self.redis.get(key)

            if raw is None:
                return None

            data = json.loads(raw)
            entry = CacheEntry(**data)
            entry.hit_count += 1

            # Update hit count in Redis
            await self.redis.setex(
                key,
                self.ttl,
                entry.model_dump_json(),
            )

            logger.debug(
                f"Keyword cache HIT | "
                f"query='{query[:40]}'"
            )

            return CacheHit(
                entry=entry,
                similarity_score=1.0,
                cache_type="keyword",
            )

        except Exception as e:
            logger.warning(f"Keyword cache get error: {e}")
            return None

    async def set(
        self,
        query: str,
        response: str,
        sources: list[str] | None = None,
        rag_context_used: bool = False,
    ) -> None:
        """Store query-response pair in keyword cache."""
        try:
            key = self._make_key(query)
            entry = CacheEntry(
                query=query,
                normalized_query=self._normalize(query),
                response=response,
                sources=sources or [],
                rag_context_used=rag_context_used,
                created_at=datetime.utcnow(),
                cache_type="keyword",
            )
            await self.redis.setex(
                key,
                self.ttl,
                entry.model_dump_json(),
            )
            logger.debug(
                f"Keyword cache SET | "
                f"query='{query[:40]}'"
            )

        except Exception as e:
            logger.warning(f"Keyword cache set error: {e}")

    async def invalidate(self, query: str) -> None:
        """Remove a specific query from cache."""
        try:
            key = self._make_key(query)
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(
                f"Keyword cache invalidate error: {e}"
            )
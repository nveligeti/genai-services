# app/modules/cache/manager.py
# Chapter 10: orchestrates keyword + semantic cache layers

from typing import Optional
from loguru import logger
from app.modules.cache.keyword_cache import KeywordCache
from app.modules.cache.schemas import CacheHit, CacheStats
from app.modules.cache.semantic_cache import SemanticCache


class CacheManager:
    """
    Two-layer cache manager.

    Chapter 10: cache lookup order:
      1. Keyword cache  (exact match, Redis)
      2. Semantic cache (similarity match, Qdrant)
      3. Miss → RAG + LLM → store in both caches

    This mirrors the book's caching hierarchy pattern.
    """

    def __init__(
        self,
        keyword_cache: KeywordCache,
        semantic_cache: SemanticCache,
        enabled: bool = True,
    ) -> None:
        self.keyword = keyword_cache
        self.semantic = semantic_cache
        self.enabled = enabled
        self._stats = CacheStats()

    async def get(
        self, query: str
    ) -> Optional[CacheHit]:
        """
        Check keyword cache first, then semantic.
        Chapter 10: fastest layer checked first.
        """
        if not self.enabled:
            return None

        self._stats.total_requests += 1

        # Layer 1 — keyword cache (exact match)
        hit = await self.keyword.get(query)
        if hit:
            self._stats.keyword_hits += 1
            logger.info(
                f"Cache HIT (keyword) | "
                f"query='{query[:40]}'"
            )
            return hit

        # Layer 2 — semantic cache (similarity)
        hit = await self.semantic.get(query)
        if hit:
            self._stats.semantic_hits += 1
            logger.info(
                f"Cache HIT (semantic) | "
                f"score={hit.similarity_score:.3f} | "
                f"query='{query[:40]}'"
            )
            return hit

        # Miss
        self._stats.misses += 1
        logger.debug(
            f"Cache MISS | query='{query[:40]}'"
        )
        return None

    async def set(
        self,
        query: str,
        response: str,
        sources: list[str] | None = None,
        rag_context_used: bool = False,
    ) -> None:
        """
        Store in BOTH keyword and semantic caches.
        Chapter 10: populate all layers on miss.
        """
        if not self.enabled:
            return

        # Store in both caches in parallel
        import asyncio
        await asyncio.gather(
            self.keyword.set(
                query, response, sources, rag_context_used
            ),
            self.semantic.set(
                query, response, sources, rag_context_used
            ),
            return_exceptions=True,
        )

    def get_stats(self) -> CacheStats:
        return self._stats

    def reset_stats(self) -> None:
        self._stats = CacheStats()


# ── Singleton factory ─────────────────────────────────────────────

_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """
    Chapter 2: DI factory for CacheManager.
    Returns disabled manager in testing.
    """
    global _cache_manager
    if _cache_manager is None:
        from app.settings import get_settings
        settings = get_settings()

        if settings.is_testing or not settings.cache_enabled:
            # Return disabled manager for tests
            _cache_manager = _make_disabled_manager()
        else:
            _cache_manager = _make_production_manager(
                settings
            )

    return _cache_manager


def _make_disabled_manager() -> CacheManager:
    """Disabled cache — used in testing."""
    from unittest.mock import AsyncMock, MagicMock
    keyword = MagicMock(spec=KeywordCache)
    keyword.get = AsyncMock(return_value=None)
    keyword.set = AsyncMock()
    semantic = MagicMock(spec=SemanticCache)
    semantic.get = AsyncMock(return_value=None)
    semantic.set = AsyncMock()
    return CacheManager(
        keyword_cache=keyword,
        semantic_cache=semantic,
        enabled=False,
    )


def _make_production_manager(settings) -> CacheManager:
    """Production cache with Redis + Qdrant."""
    import redis.asyncio as aioredis
    from qdrant_client import AsyncQdrantClient
    from app.providers.embedder import get_embedder

    redis_client = aioredis.from_url(settings.redis_url)
    qdrant_client = AsyncQdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )

    keyword = KeywordCache(
        redis_client=redis_client,
        ttl=settings.keyword_cache_ttl,
    )
    semantic = SemanticCache(
        qdrant_client=qdrant_client,
        embedder=get_embedder(),
        threshold=settings.semantic_cache_threshold,
        max_entries=settings.semantic_cache_max_entries,
        dimension=settings.embedding_dimension,
    )
    return CacheManager(
        keyword_cache=keyword,
        semantic_cache=semantic,
        enabled=settings.cache_enabled,
    )


def reset_cache_manager() -> None:
    """Reset singleton — used in tests."""
    global _cache_manager
    _cache_manager = None
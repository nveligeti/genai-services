# tests/unit/test_keyword_cache.py
# Chapter 11: unit tests for keyword cache

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.cache.keyword_cache import KeywordCache


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def cache(mock_redis):
    return KeywordCache(redis_client=mock_redis, ttl=3600)


class TestKeywordCache:

    def test_make_key_normalizes_query(self, cache):
        """
        Chapter 10: case + whitespace normalization.
        Chapter 11: invariance test.
        """
        k1 = cache._make_key("What are payment terms?")
        k2 = cache._make_key("what are payment terms?")
        k3 = cache._make_key("  WHAT ARE PAYMENT TERMS?  ")
        assert k1 == k2 == k3

    def test_different_queries_different_keys(self, cache):
        """DET — different queries must differ."""
        k1 = cache._make_key("payment terms")
        k2 = cache._make_key("termination clauses")
        assert k1 != k2

    def test_key_starts_with_prefix(self, cache):
        """Chapter 11: key format contract."""
        key = cache._make_key("test query")
        assert key.startswith("keyword:")

    @pytest.mark.asyncio
    async def test_get_returns_none_on_miss(
        self, cache, mock_redis
    ):
        """Chapter 11: boundary — cache miss."""
        mock_redis.get = AsyncMock(return_value=None)
        result = await cache.get("unknown query")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_hit_on_match(
        self, cache, mock_redis
    ):
        """Chapter 11: happy path — cache hit."""
        from app.modules.cache.schemas import CacheEntry
        import json
        from datetime import datetime

        entry = CacheEntry(
            query="test query",
            normalized_query="test query",
            response="test response",
            sources=[],
            created_at=datetime.utcnow(),
        )
        mock_redis.get = AsyncMock(
            return_value=entry.model_dump_json().encode()
        )

        result = await cache.get("test query")
        assert result is not None
        assert result.cache_type == "keyword"
        assert result.similarity_score == 1.0

    @pytest.mark.asyncio
    async def test_set_calls_redis_setex(
        self, cache, mock_redis
    ):
        """
        Chapter 11: spy pattern — verify Redis called.
        """
        await cache.set(
            "test query",
            "test response",
            sources=["doc.pdf"],
        )
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_error_returns_none_not_raises(
        self, cache, mock_redis
    ):
        """
        Chapter 9 / 11: fail-open behavior.
        Cache errors must not crash the request.
        """
        mock_redis.get = AsyncMock(
            side_effect=Exception("Redis down")
        )
        result = await cache.get("test query")
        assert result is None   # fail-open ✅
# tests/unit/test_cache_manager.py
# Chapter 11: unit tests for CacheManager

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.cache.manager import CacheManager
from app.modules.cache.keyword_cache import KeywordCache
from app.modules.cache.semantic_cache import SemanticCache


@pytest.fixture
def mock_keyword():
    kw = MagicMock(spec=KeywordCache)
    kw.get = AsyncMock(return_value=None)
    kw.set = AsyncMock()
    return kw


@pytest.fixture
def mock_semantic():
    sem = MagicMock(spec=SemanticCache)
    sem.get = AsyncMock(return_value=None)
    sem.set = AsyncMock()
    return sem


@pytest.fixture
def manager(mock_keyword, mock_semantic):
    return CacheManager(
        keyword_cache=mock_keyword,
        semantic_cache=mock_semantic,
        enabled=True,
    )


class TestCacheManager:

    @pytest.mark.asyncio
    async def test_checks_keyword_before_semantic(
        self, manager, mock_keyword, mock_semantic
    ):
        """
        Chapter 10: keyword checked first.
        Chapter 11: verify call order with spy.
        """
        call_order = []

        async def track_keyword(query):
            call_order.append("keyword")
            return None

        async def track_semantic(query):
            call_order.append("semantic")
            return None

        mock_keyword.get = track_keyword
        mock_semantic.get = track_semantic

        await manager.get("test query")

        assert call_order == ["keyword", "semantic"]

    @pytest.mark.asyncio
    async def test_returns_keyword_hit_without_semantic(
        self, manager, mock_keyword, mock_semantic
    ):
        """
        Chapter 11: keyword hit skips semantic.
        Spy: semantic.get never called on keyword hit.
        """
        from app.modules.cache.schemas import (
            CacheEntry, CacheHit
        )
        from datetime import datetime

        mock_hit = CacheHit(
            entry=CacheEntry(
                query="q",
                normalized_query="q",
                response="r",
                created_at=datetime.utcnow(),
            ),
            similarity_score=1.0,
            cache_type="keyword",
        )
        mock_keyword.get = AsyncMock(return_value=mock_hit)

        result = await manager.get("test query")

        assert result is not None
        assert result.cache_type == "keyword"
        mock_semantic.get.assert_not_called()   # ← spy ✅

    @pytest.mark.asyncio
    async def test_set_stores_in_both_caches(
        self, manager, mock_keyword, mock_semantic
    ):
        """
        Chapter 10: both caches populated on miss.
        Chapter 11: verify both set() called.
        """
        await manager.set(
            "query", "response", sources=["doc.pdf"]
        )

        mock_keyword.set.assert_called_once()
        mock_semantic.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_disabled_manager_always_misses(
        self, mock_keyword, mock_semantic
    ):
        """
        Chapter 11: disabled cache → always None.
        Chapter 10: cache.enabled=False for testing.
        """
        disabled = CacheManager(
            keyword_cache=mock_keyword,
            semantic_cache=mock_semantic,
            enabled=False,
        )
        result = await disabled.get("any query")
        assert result is None
        mock_keyword.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_stats_track_hits_and_misses(
        self, manager, mock_keyword, mock_semantic
    ):
        """
        Chapter 10: stats tracking.
        Chapter 11: state after multiple calls.
        """
        from app.modules.cache.schemas import (
            CacheEntry, CacheHit
        )
        from datetime import datetime

        mock_hit = CacheHit(
            entry=CacheEntry(
                query="q",
                normalized_query="q",
                response="r",
                created_at=datetime.utcnow(),
            ),
            similarity_score=1.0,
            cache_type="keyword",
        )

        # 2 misses
        await manager.get("miss 1")
        await manager.get("miss 2")

        # 1 keyword hit
        mock_keyword.get = AsyncMock(return_value=mock_hit)
        await manager.get("hit 1")

        stats = manager.get_stats()
        assert stats.total_requests == 3
        assert stats.keyword_hits == 1
        assert stats.misses == 2
        assert stats.hit_rate == pytest.approx(
            1 / 3, abs=0.01
        )
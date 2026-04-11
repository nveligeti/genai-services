# tests/unit/test_semantic_cache.py
# Chapter 11: unit tests for semantic cache

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.cache.semantic_cache import SemanticCache
from app.providers.embedder import MockEmbedder


@pytest.fixture
def mock_qdrant():
    client = MagicMock()
    client.get_collections = AsyncMock(
        return_value=MagicMock(collections=[])
    )
    client.create_collection = AsyncMock()
    client.search = AsyncMock(return_value=[])
    client.upsert = AsyncMock()
    return client


@pytest.fixture
def embedder():
    return MockEmbedder(dimension=384)


@pytest.fixture
def cache(mock_qdrant, embedder):
    return SemanticCache(
        qdrant_client=mock_qdrant,
        embedder=embedder,
        threshold=0.92,
        dimension=384,
    )


class TestSemanticCache:

    @pytest.mark.asyncio
    async def test_get_returns_none_when_no_results(
        self, cache, mock_qdrant
    ):
        """Chapter 11: boundary — empty search results."""
        mock_qdrant.search = AsyncMock(return_value=[])
        result = await cache.get("test query")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_hit_above_threshold(
        self, cache, mock_qdrant
    ):
        """
        Chapter 11: boundary — score above threshold.
        Chapter 10: threshold=0.92 → scores >= 0.92 hit.
        """
        from datetime import datetime
        mock_result = MagicMock()
        mock_result.score = 0.95
        mock_result.payload = {
            "query": "similar query",
            "normalized_query": "similar query",
            "response": "cached response",
            "sources": ["doc.pdf"],
            "rag_context_used": False,
            "created_at": datetime.utcnow().isoformat(),
            "hit_count": 0,
        }
        mock_qdrant.search = AsyncMock(
            return_value=[mock_result]
        )

        result = await cache.get("test query")
        assert result is not None
        assert result.similarity_score == 0.95
        assert result.cache_type == "semantic"

    @pytest.mark.asyncio
    async def test_set_calls_qdrant_upsert(
        self, cache, mock_qdrant
    ):
        """Chapter 11: spy — verify Qdrant called."""
        await cache.set(
            "test query",
            "test response",
            sources=["doc.pdf"],
        )
        mock_qdrant.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_returns_none_not_raises(
        self, cache, mock_qdrant
    ):
        """Chapter 9: fail-open behavior."""
        mock_qdrant.search = AsyncMock(
            side_effect=Exception("Qdrant down")
        )
        result = await cache.get("test query")
        assert result is None   # fail-open ✅
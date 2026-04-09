# tests/unit/test_rag_pipeline.py
# Chapter 11: unit tests for RAG pipeline

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.rag.pipeline import RAGPipeline
from app.modules.rag.schemas import RAGQueryRequest
from app.providers.embedder import MockEmbedder


@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    repo.search = AsyncMock(return_value=[])
    repo.upsert_chunks = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def embedder():
    return MockEmbedder(dimension=384)


@pytest.fixture
def pipeline(mock_repository, embedder):
    return RAGPipeline(
        repository=mock_repository,
        embedder=embedder,
    )


class TestRAGPipelineChunking:

    def test_chunk_text_splits_correctly(self, pipeline):
        """Unit test — chunking logic."""
        text = "word " * 200  # 1000 chars
        chunks = pipeline._chunk_text(text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.original_text) <= pipeline.chunk_size

    def test_chunk_text_respects_overlap(self, pipeline):
        """
        IT — overlap means adjacent chunks share content.
        Chapter 11: invariance of overlap behavior.
        """
        pipeline.chunk_size = 100
        pipeline.chunk_overlap = 20
        text = "a" * 200
        chunks = pipeline._chunk_text(text)
        assert len(chunks) >= 2

    def test_clean_text_removes_extra_whitespace(self, pipeline):
        """Unit test — text cleaning."""
        dirty = "hello    world\n\ntest   "
        cleaned = pipeline._clean_text(dirty)
        assert "  " not in cleaned
        assert cleaned == cleaned.strip()


class TestRAGPipelineQuery:

    @pytest.mark.asyncio
    async def test_query_calls_repository_search(
        self, pipeline, mock_repository
    ):
        """
        Integration test — query must call repository.
        Chapter 11: spy pattern.
        """
        request = RAGQueryRequest(query="What is FastAPI?")
        await pipeline.query(request)
        mock_repository.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_returns_correct_structure(
        self, pipeline
    ):
        """
        Integration test — response contract.
        Chapter 11: nonbrittle contract assertion.
        """
        request = RAGQueryRequest(query="test query")
        response = await pipeline.query(request)

        assert response.query == "test query"
        assert isinstance(response.results, list)
        assert isinstance(response.context, str)
        assert response.total_results == len(response.results)

    @pytest.mark.asyncio
    async def test_query_with_no_results_returns_no_context(
        self, pipeline, mock_repository
    ):
        """
        Boundary test — empty results handled gracefully.
        Chapter 11: boundary condition.
        """
        mock_repository.search = AsyncMock(return_value=[])
        request = RAGQueryRequest(query="obscure query")
        response = await pipeline.query(request)

        assert response.total_results == 0
        assert "No relevant context" in response.context

    @pytest.mark.asyncio
    async def test_query_embeds_before_searching(
        self, pipeline, mock_repository, embedder
    ):
        """
        Integration test — verify embed called before search.
        Chapter 11: verify correct interaction sequence.
        """
        call_order = []

        original_embed = embedder.embed
        def tracked_embed(text):
            call_order.append("embed")
            return original_embed(text)

        original_search = mock_repository.search
        async def tracked_search(*args, **kwargs):
            call_order.append("search")
            return []

        embedder.embed = tracked_embed
        mock_repository.search = tracked_search

        await pipeline.query(RAGQueryRequest(query="test"))

        assert call_order == ["embed", "search"]
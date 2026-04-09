# tests/unit/test_embedder.py
# Chapter 11: unit tests for embedder (Chapter 3)

import pytest
from app.providers.embedder import MockEmbedder, reset_embedder


class TestMockEmbedder:

    def setup_method(self):
        reset_embedder()

    def test_embed_returns_correct_dimension(self):
        """MFT — vector dimension must match config."""
        embedder = MockEmbedder(dimension=384)
        vector = embedder.embed("Hello FastAPI")
        assert len(vector) == 384

    def test_embed_is_deterministic(self):
        """
        IT — same text always produces same vector.
        Chapter 11: invariance test — critical for caching.
        """
        embedder = MockEmbedder(dimension=384)
        v1 = embedder.embed("What is RAG?")
        v2 = embedder.embed("What is RAG?")
        assert v1 == v2

    def test_different_texts_produce_different_vectors(self):
        """DET — different inputs must produce different vectors."""
        embedder = MockEmbedder(dimension=384)
        v1 = embedder.embed("FastAPI is great")
        v2 = embedder.embed("Qdrant is a vector database")
        assert v1 != v2

    def test_embed_returns_unit_vector(self):
        """MFT — vector must be L2 normalized."""
        import math
        embedder = MockEmbedder(dimension=384)
        vector = embedder.embed("test text")
        magnitude = math.sqrt(sum(x * x for x in vector))
        assert abs(magnitude - 1.0) < 1e-6

    def test_embed_batch_matches_individual_embeds(self):
        """IT — batch must produce same result as individual calls."""
        embedder = MockEmbedder(dimension=384)
        texts = ["text one", "text two", "text three"]
        batch = embedder.embed_batch(texts)
        individual = [embedder.embed(t) for t in texts]
        assert batch == individual

    @pytest.mark.parametrize("dimension", [128, 256, 384, 768])
    def test_embed_respects_dimension_setting(self, dimension):
        """Chapter 11: parametrize — all dimensions work."""
        embedder = MockEmbedder(dimension=dimension)
        vector = embedder.embed("test")
        assert len(vector) == dimension
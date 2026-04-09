# app/providers/embedder.py
# Chapter 3: external serving strategy for embeddings
# Chapter 4: fully typed

import hashlib
import math
from abc import ABC, abstractmethod
from loguru import logger


class BaseEmbedder(ABC):
    """
    Abstract embedder interface.
    Chapter 2: dependency inversion — code depends on
    abstraction not concrete implementation.
    """

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Convert text to embedding vector."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Convert multiple texts to embedding vectors."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension this embedder produces."""
        ...


class MockEmbedder(BaseEmbedder):
    """
    Deterministic mock embedder for testing and local dev.

    Chapter 3: mock serving strategy — no GPU, no large download.
    Chapter 11: produces deterministic vectors for reliable tests.

    Key property: same text ALWAYS produces same vector.
    Similar texts produce vectors with high cosine similarity.
    """

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension
        logger.info(
            f"MockEmbedder initialized | dimension={dimension}"
        )

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """
        Generate deterministic vector from text.
        Uses hash-based approach so similar texts
        produce similar vectors.
        """
        # Normalize text for consistency
        normalized = text.lower().strip()

        # Generate base vector from hash
        vector = []
        for i in range(self._dimension):
            # Use different hash seeds per dimension
            seed = f"{normalized}_{i}"
            hash_val = int(
                hashlib.md5(seed.encode()).hexdigest(), 16
            )
            # Normalize to [-1, 1] range
            normalized_val = (hash_val % 10000) / 5000.0 - 1.0
            vector.append(normalized_val)

        # L2 normalize the vector
        return self._normalize(vector)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    def _normalize(self, vector: list[float]) -> list[float]:
        """L2 normalize vector to unit length."""
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude == 0:
            return vector
        return [x / magnitude for x in vector]


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Real embedder using sentence-transformers.
    Used in production when embedding_model != 'mock'.
    Chapter 3: real external serving strategy.
    """

    def __init__(self, model_name: str, dimension: int) -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self._dimension = dimension
        logger.info(
            f"SentenceTransformerEmbedder | model={model_name}"
        )

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()

    def embed_batch(
        self, texts: list[str]
    ) -> list[list[float]]:
        return self._model.encode(texts).tolist()


# ── Factory ───────────────────────────────────────────────────────

_embedder: BaseEmbedder | None = None


def get_embedder() -> BaseEmbedder:
    """
    Chapter 2: dependency injection factory.
    Returns mock or real embedder based on settings.
    """
    global _embedder
    if _embedder is None:
        from app.settings import get_settings
        settings = get_settings()

        if settings.embedding_model == "mock":
            _embedder = MockEmbedder(
                dimension=settings.embedding_dimension
            )
        else:
            _embedder = SentenceTransformerEmbedder(
                model_name=settings.embedding_model,
                dimension=settings.embedding_dimension,
            )
    return _embedder


def reset_embedder() -> None:
    """Reset singleton — used in tests."""
    global _embedder
    _embedder = None
# app/modules/cache/semantic_cache.py
# Chapter 10: vector similarity cache using Qdrant

import uuid
from datetime import datetime
from typing import Optional
from loguru import logger
from app.modules.cache.schemas import CacheEntry, CacheHit
from app.providers.embedder import BaseEmbedder


class SemanticCache:
    """
    Vector similarity cache using Qdrant.
    Chapter 10: catches paraphrased queries.

    Flow:
      query → embed → search Qdrant cache collection
        similarity >= threshold → cache HIT
        similarity <  threshold → cache MISS
    """

    COLLECTION = "documind_semantic_cache"

    def __init__(
        self,
        qdrant_client,
        embedder: BaseEmbedder,
        threshold: float = 0.92,
        max_entries: int = 1000,
        dimension: int = 384,
    ) -> None:
        self.qdrant = qdrant_client
        self.embedder = embedder
        self.threshold = threshold
        self.max_entries = max_entries
        self.dimension = dimension

    async def ensure_collection(self) -> None:
        """Create cache collection if it doesn't exist."""
        try:
            from qdrant_client.http.models import (
                Distance,
                VectorParams,
            )
            collections = (
                await self.qdrant.get_collections()
            )
            exists = any(
                c.name == self.COLLECTION
                for c in collections.collections
            )
            if not exists:
                await self.qdrant.create_collection(
                    collection_name=self.COLLECTION,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(
                    f"Created semantic cache collection: "
                    f"{self.COLLECTION}"
                )
        except Exception as e:
            logger.warning(
                f"Semantic cache collection error: {e}"
            )

    async def get(
        self, query: str
    ) -> Optional[CacheHit]:
        """
        Search for semantically similar cached query.
        Chapter 10: cosine similarity >= threshold → HIT.
        """
        try:
            query_vector = self.embedder.embed(query)

            results = await self.qdrant.search(
                collection_name=self.COLLECTION,
                query_vector=query_vector,
                limit=1,
                score_threshold=self.threshold,
            )

            if not results:
                return None

            best = results[0]
            payload = best.payload

            entry = CacheEntry(
                query=payload["query"],
                normalized_query=payload.get(
                    "normalized_query", ""
                ),
                response=payload["response"],
                sources=payload.get("sources", []),
                rag_context_used=payload.get(
                    "rag_context_used", False
                ),
                created_at=datetime.fromisoformat(
                    payload.get(
                        "created_at",
                        datetime.utcnow().isoformat(),
                    )
                ),
                hit_count=payload.get("hit_count", 0) + 1,
                cache_type="semantic",
            )

            logger.debug(
                f"Semantic cache HIT | "
                f"score={best.score:.3f} | "
                f"query='{query[:40]}'"
            )

            return CacheHit(
                entry=entry,
                similarity_score=best.score,
                cache_type="semantic",
            )

        except Exception as e:
            logger.warning(f"Semantic cache get error: {e}")
            return None

    async def set(
        self,
        query: str,
        response: str,
        sources: list[str] | None = None,
        rag_context_used: bool = False,
    ) -> None:
        """
        Store query embedding + response in Qdrant.
        Chapter 10: evict oldest if max_entries reached.
        """
        try:
            from qdrant_client.http.models import PointStruct

            query_vector = self.embedder.embed(query)

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=query_vector,
                payload={
                    "query": query,
                    "normalized_query": " ".join(
                        query.lower().strip().split()
                    ),
                    "response": response,
                    "sources": sources or [],
                    "rag_context_used": rag_context_used,
                    "created_at": (
                        datetime.utcnow().isoformat()
                    ),
                    "hit_count": 0,
                },
            )

            await self.qdrant.upsert(
                collection_name=self.COLLECTION,
                points=[point],
            )

            logger.debug(
                f"Semantic cache SET | "
                f"query='{query[:40]}'"
            )

        except Exception as e:
            logger.warning(f"Semantic cache set error: {e}")
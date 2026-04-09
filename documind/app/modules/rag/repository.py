# app/modules/rag/repository.py
# Chapter 7: repository pattern for vector database
# Chapter 5: async Qdrant client

import uuid
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    ScoredPoint,
    VectorParams,
)
from app.modules.rag.schemas import ChunkMetadata, SearchResult


class VectorRepository:
    """
    Async repository for Qdrant vector database.

    Chapter 7: repository pattern abstracts all
    database operations behind clean CRUD interface.
    Chapter 5: fully async using AsyncQdrantClient.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "documind",
        dimension: int = 384,
    ) -> None:
        self.client = AsyncQdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.dimension = dimension

    async def ensure_collection(self) -> None:
        """
        Create collection if it doesn't exist.
        Called during lifespan startup (Chapter 5).
        """
        collections = await self.client.get_collections()
        exists = any(
            c.name == self.collection_name
            for c in collections.collections
        )

        if not exists:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(
                f"Created Qdrant collection: {self.collection_name}"
            )
        else:
            logger.info(
                f"Qdrant collection exists: {self.collection_name}"
            )

    async def upsert_chunks(
        self,
        chunks: list[ChunkMetadata],
        vectors: list[list[float]],
    ) -> int:
        """
        Store text chunks with their embedding vectors.
        Chapter 7: create operation in repository pattern.
        """
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "document_id":   chunk.document_id,
                    "filename":      chunk.filename,
                    "chunk_index":   chunk.chunk_index,
                    "original_text": chunk.original_text,
                    "chunk_size":    chunk.chunk_size,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        await self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        logger.info(
            f"Upserted {len(points)} chunks | "
            f"collection={self.collection_name}"
        )
        return len(points)

    async def search(
        self,
        query_vector: list[float],
        limit: int = 3,
        score_threshold: float = 0.5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        """
        Semantic search over stored vectors.
        Chapter 5: cosine similarity search.
        Chapter 7: read operation in repository pattern.
        """
        query_filter = None
        if document_id:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            )

        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [
            SearchResult(
                document_id=r.payload["document_id"],
                filename=r.payload["filename"],
                chunk_index=r.payload["chunk_index"],
                original_text=r.payload["original_text"],
                score=r.score,
            )
            for r in results
        ]

    async def delete_document_chunks(
        self, document_id: str
    ) -> None:
        """
        Delete all chunks for a document.
        Chapter 7: delete operation in repository pattern.
        """
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(
                                value=document_id
                            ),
                        )
                    ]
                )
            ),
        )
        logger.info(
            f"Deleted chunks for document: {document_id}"
        )

    async def count(self) -> int:
        """Return total number of vectors in collection."""
        result = await self.client.count(
            collection_name=self.collection_name
        )
        return result.count
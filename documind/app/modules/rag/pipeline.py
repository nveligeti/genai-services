# app/modules/rag/pipeline.py
# Chapter 5: full RAG pipeline — chunk, embed, store, retrieve

import re
from loguru import logger
from app.modules.rag.repository import VectorRepository
from app.modules.rag.schemas import (
    ChunkMetadata,
    IndexDocumentResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    SearchResult,
)
from app.providers.embedder import BaseEmbedder
from app.settings import get_settings
import aiofiles
from pathlib import Path


class RAGPipeline:
    """
    Orchestrates the full RAG pipeline.

    Chapter 5: combines async file I/O, embedding,
    and vector database operations.
    Chapter 7: uses VectorRepository for all DB ops.
    """

    def __init__(
        self,
        repository: VectorRepository,
        embedder: BaseEmbedder,
    ) -> None:
        self.repository = repository
        self.embedder = embedder
        settings = get_settings()
        self.chunk_size = settings.rag_chunk_size
        self.chunk_overlap = settings.rag_chunk_overlap

    async def index_document(
        self,
        document_id: str,
        filename: str,
        text_filepath: str,
    ) -> IndexDocumentResponse:
        """
        Full indexing pipeline:
        1. Load text from file (async)
        2. Clean and chunk text
        3. Embed each chunk
        4. Store in Qdrant

        Chapter 5: async throughout, called as background task.
        """
        logger.info(
            f"Indexing document | id={document_id} "
            f"file={filename}"
        )

        # Step 1 — Load text
        text = await self._load_text(text_filepath)
        if not text.strip():
            logger.warning(
                f"Empty text for document: {document_id}"
            )
            return IndexDocumentResponse(
                document_id=document_id,
                filename=filename,
                chunks_indexed=0,
                message="Document has no extractable text",
            )

        # Step 2 — Clean and chunk
        cleaned = self._clean_text(text)
        chunks = self._chunk_text(cleaned)

        logger.info(
            f"Created {len(chunks)} chunks | id={document_id}"
        )

        # Step 3 — Embed all chunks
        chunk_texts = [c.original_text for c in chunks]
        vectors = self.embedder.embed_batch(chunk_texts)

        # Attach document metadata to chunks
        metadata_chunks = [
            ChunkMetadata(
                document_id=document_id,
                filename=filename,
                chunk_index=i,
                original_text=chunk.original_text,
                chunk_size=len(chunk.original_text),
            )
            for i, chunk in enumerate(chunks)
        ]

        # Step 4 — Store in Qdrant
        count = await self.repository.upsert_chunks(
            metadata_chunks, vectors
        )

        return IndexDocumentResponse(
            document_id=document_id,
            filename=filename,
            chunks_indexed=count,
            message=(
                f"Successfully indexed {count} chunks "
                f"from {filename}"
            ),
        )

    async def query(
        self, request: RAGQueryRequest
    ) -> RAGQueryResponse:
        """
        Full retrieval pipeline:
        1. Embed the query
        2. Search Qdrant for similar chunks
        3. Build context string for LLM

        Chapter 5: semantic search via cosine similarity.
        """
        logger.info(
            f"RAG query | query='{request.query[:50]}...' "
            f"limit={request.limit}"
        )

        # Step 1 — Embed query
        query_vector = self.embedder.embed(request.query)

        # Step 2 — Search
        results = await self.repository.search(
            query_vector=query_vector,
            limit=request.limit,
            score_threshold=request.score_threshold,
        )

        # Step 3 — Build context
        context = self._build_context(results)

        logger.info(
            f"RAG retrieved {len(results)} chunks | "
            f"query='{request.query[:30]}'"
        )

        return RAGQueryResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            context=context,
        )

    # ── Private helpers ───────────────────────────────────────────

    async def _load_text(self, filepath: str) -> str:
        """Async file read — Chapter 5."""
        async with aiofiles.open(
            filepath, "r", encoding="utf-8", errors="replace"
        ) as f:
            return await f.read()

    def _clean_text(self, text: str) -> str:
        """Remove noise from extracted text."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\. ,", "", text)
        text = text.replace("..", ".")
        return text.strip()

    def _chunk_text(
        self, text: str
    ) -> list["_Chunk"]:
        """
        Split text into overlapping chunks.
        Chapter 5: chunk_size and overlap from settings.
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append(_Chunk(original_text=chunk_text))

            # Move forward with overlap
            start += self.chunk_size - self.chunk_overlap

        return chunks

    def _build_context(
        self, results: list[SearchResult]
    ) -> str:
        """
        Concatenate retrieved chunks into LLM context.
        Chapter 10: context ordering matters for LLM quality.
        Results already sorted by score descending.
        """
        if not results:
            return "No relevant context found in documents."

        parts = []
        for i, result in enumerate(results, 1):
            parts.append(
                f"[Source {i}: {result.filename} "
                f"(relevance: {result.score:.2f})]\n"
                f"{result.original_text}"
            )

        return "\n\n---\n\n".join(parts)


class _Chunk:
    """Internal chunk representation."""
    def __init__(self, original_text: str) -> None:
        self.original_text = original_text
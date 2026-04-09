# app/modules/rag/schemas.py
# Chapter 4: type-safe RAG request/response

from pydantic import BaseModel, Field
from typing import Annotated


class ChunkMetadata(BaseModel):
    """Metadata stored alongside each vector in Qdrant."""
    document_id: str
    filename: str
    chunk_index: int
    original_text: str
    chunk_size: int


class SearchResult(BaseModel):
    """A single retrieved chunk with its similarity score."""
    document_id: str
    filename: str
    chunk_index: int
    original_text: str
    score: float


class RAGQueryRequest(BaseModel):
    """Request to query the RAG knowledge base."""
    query: Annotated[
        str,
        Field(min_length=1, max_length=2000)
    ]
    limit: Annotated[
        int,
        Field(default=3, ge=1, le=10)
    ] = 3
    score_threshold: Annotated[
        float,
        Field(default=0.5, ge=0.0, le=1.0)
    ] = 0.5


class RAGQueryResponse(BaseModel):
    """Response from RAG query."""
    query: str
    results: list[SearchResult]
    total_results: int
    context: str  # concatenated text for LLM prompt


class IndexDocumentResponse(BaseModel):
    """Response after indexing a document into Qdrant."""
    document_id: str
    filename: str
    chunks_indexed: int
    message: str
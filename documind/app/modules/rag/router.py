# app/modules/rag/router.py
# Chapter 2: modular router
# Chapter 5: dependency injection for repository + pipeline

from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends
from app.modules.rag.pipeline import RAGPipeline
from app.modules.rag.repository import VectorRepository
from app.modules.rag.schemas import (
    IndexDocumentResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.providers.embedder import get_embedder
from app.settings import get_settings

router = APIRouter(prefix="/rag", tags=["RAG"])


def get_vector_repository() -> VectorRepository:
    """Chapter 2: DI factory for VectorRepository."""
    settings = get_settings()
    return VectorRepository(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.rag_collection_name,
        dimension=settings.embedding_dimension,
    )


def get_rag_pipeline(
    repository: Annotated[
        VectorRepository, Depends(get_vector_repository)
    ],
) -> RAGPipeline:
    """Chapter 2: DI factory for RAGPipeline."""
    return RAGPipeline(
        repository=repository,
        embedder=get_embedder(),
    )


RAGPipelineDep = Annotated[
    RAGPipeline, Depends(get_rag_pipeline)
]


@router.post(
    "/index/{document_id}",
    response_model=IndexDocumentResponse,
    summary="Index a document into the vector store",
)
async def index_document_controller(
    document_id: str,
    background_tasks: BackgroundTasks,
    pipeline: RAGPipelineDep,
) -> IndexDocumentResponse:
    """
    Index an already-uploaded document into Qdrant.
    Chapter 5: triggers background task for heavy embedding.
    """
    from app.modules.documents.service import (
        DocumentService, _document_store
    )

    doc = _document_store.get(document_id)
    if not doc:
        from app.exceptions import NotFoundException
        raise NotFoundException("Document", document_id)

    text_filepath = doc["filepath"].replace(".pdf", ".txt").replace(
        doc["filename"],
        doc["filename"].replace(
            doc["filename"].split(".")[-1], "txt"
        ),
    )

    # Run indexing as background task
    # Chapter 5: non-blocking — returns immediately
    background_tasks.add_task(
        pipeline.index_document,
        document_id,
        doc["filename"],
        text_filepath,
    )

    return IndexDocumentResponse(
        document_id=document_id,
        filename=doc["filename"],
        chunks_indexed=0,
        message="Indexing started in background",
    )


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Query the knowledge base",
)
async def query_knowledge_base_controller(
    request: RAGQueryRequest,
    pipeline: RAGPipelineDep,
) -> RAGQueryResponse:
    """
    Semantic search across all indexed documents.
    Chapter 5: embedding + cosine similarity search.
    """
    return await pipeline.query(request)
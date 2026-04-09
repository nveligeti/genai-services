# app/modules/chat/router.py
# Chapter 6: SSE streaming endpoint
# Chapter 2: dependency injection

from typing import Annotated, AsyncGenerator
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.modules.chat.schemas import ChatRequest, ChatResponse
from app.modules.chat.service import ChatService
from app.modules.rag.pipeline import RAGPipeline
from app.modules.rag.repository import VectorRepository
from app.providers.embedder import get_embedder
from app.providers.llm import get_llm_client
from app.settings import get_settings

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_rag_pipeline() -> RAGPipeline:
    """Chapter 2: DI factory — RAG pipeline for chat."""
    settings = get_settings()
    repository = VectorRepository(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.rag_collection_name,
        dimension=settings.embedding_dimension,
    )
    return RAGPipeline(
        repository=repository,
        embedder=get_embedder(),
    )


def get_chat_service(
    rag_pipeline: Annotated[
        RAGPipeline, Depends(get_rag_pipeline)
    ],
) -> ChatService:
    """Chapter 2: DI factory — ChatService."""
    return ChatService(
        llm_client=get_llm_client(),
        rag_pipeline=rag_pipeline,
    )


ChatServiceDep = Annotated[
    ChatService, Depends(get_chat_service)
]


@router.post(
    "/stream",
    summary="Stream a chat response via SSE",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "SSE stream of chat tokens",
        }
    },
)
async def chat_stream_controller(
    request: ChatRequest,
    service: ChatServiceDep,
) -> StreamingResponse:
    """
    Stream LLM response token by token via SSE.

    Chapter 6: StreamingResponse with text/event-stream.
    Chapter 5: async generator as data source.
    Chapter 10: RAG context injected into prompt.

    Event format:
        data: {"type": "rag",   "content": "", "metadata": {...}}
        data: {"type": "token", "content": "Hello", "metadata": {}}
        data: {"type": "done",  "content": "", "metadata": {...}}
        data: {"type": "error", "content": "...", "metadata": {}}
    """
    return StreamingResponse(
        service.chat_stream(request),
        media_type="text/event-stream",
        headers={
            # Prevent buffering in proxies/nginx
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "",
    response_model=ChatResponse,
    summary="Non-streaming chat (for testing)",
)
async def chat_controller(
    request: ChatRequest,
    service: ChatServiceDep,
) -> ChatResponse:
    """
    Non-streaming chat endpoint.
    Useful for testing and simple integrations
    that don't support SSE.
    Chapter 6: same service, different response format.
    """
    return await service.chat(request)
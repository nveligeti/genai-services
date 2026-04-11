# app/modules/chat/router.py — replace entire file

from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.modules.auth.dependencies import CurrentUserDep
from app.modules.chat.schemas import ChatRequest, ChatResponse
from app.modules.chat.service import ChatService
from app.modules.guardrails.pipeline import (
    GuardrailPipeline,
    get_guardrail_pipeline,
)
from app.modules.rag.pipeline import RAGPipeline
from app.modules.rag.repository import VectorRepository
from app.providers.embedder import get_embedder
from app.providers.llm import get_llm_client
from app.settings import get_settings

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_rag_pipeline() -> RAGPipeline:
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
    guardrail_pipeline: Annotated[
        GuardrailPipeline,
        Depends(get_guardrail_pipeline),
    ],
) -> ChatService:
    return ChatService(
        llm_client=get_llm_client(),
        rag_pipeline=rag_pipeline,
        guardrail_pipeline=guardrail_pipeline,
    )


ChatServiceDep = Annotated[
    ChatService, Depends(get_chat_service)
]


@router.post("/stream", response_class=StreamingResponse)
async def chat_stream_controller(
    request: Request,
    body: ChatRequest,
    service: ChatServiceDep,
    current_user: CurrentUserDep,
) -> StreamingResponse:
    return StreamingResponse(
        service.chat_stream(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("", response_model=ChatResponse)
async def chat_controller(
    request: Request,
    body: ChatRequest,
    service: ChatServiceDep,
    current_user: CurrentUserDep,
) -> ChatResponse:
    return await service.chat(body)
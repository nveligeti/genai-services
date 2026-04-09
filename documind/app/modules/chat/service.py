# app/modules/chat/service.py
# Chapter 10: prompt engineering — RCT template
# Chapter 5: combines RAG retrieval with LLM generation

from loguru import logger
from app.modules.chat.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    MessageRole,
)
from app.modules.rag.pipeline import RAGPipeline
from app.modules.rag.schemas import RAGQueryRequest
from app.providers.llm import MockLLMClient
from typing import AsyncGenerator


# Chapter 10: RCT prompt template
# Role — Context — Task
SYSTEM_PROMPT_WITH_RAG = """
You are DocuMind, an intelligent document assistant.

## Role
You help users understand and extract insights from
their uploaded documents. You are precise, helpful,
and always ground your answers in the provided context.

## Context
Use ONLY the document context below to answer questions.
If the context does not contain enough information,
say so clearly rather than guessing.

## Task
Answer the user's question based on the context provided.
Be concise, accurate, and cite the source documents
when relevant.

## Document Context
{context}
""".strip()

SYSTEM_PROMPT_WITHOUT_RAG = """
You are DocuMind, an intelligent document assistant.
Answer the user's question helpfully and concisely.
If you don't know something, say so clearly.
""".strip()


class ChatService:
    """
    Orchestrates RAG retrieval + LLM generation.

    Chapter 10: prompt engineering with RCT template.
    Chapter 5: async throughout.
    Chapter 6: supports both streaming and non-streaming.
    """

    def __init__(
        self,
        llm_client: MockLLMClient,
        rag_pipeline: RAGPipeline | None = None,
    ) -> None:
        self.llm = llm_client
        self.rag = rag_pipeline

    async def chat(
        self, request: ChatRequest
    ) -> ChatResponse:
        """
        Non-streaming chat.
        Used for testing and simple integrations.
        """
        system_prompt, sources, rag_used = (
            await self._build_prompt(request)
        )

        response_text = await self.llm.generate(
            prompt=request.message,
            system_prompt=system_prompt,
            temperature=request.temperature,
        )

        return ChatResponse(
            message=response_text,
            rag_context_used=rag_used,
            sources=sources,
            prompt_tokens=len(
                (system_prompt + request.message).split()
            ),
        )

    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        SSE streaming chat.
        Chapter 6: yields SSE-formatted strings.
        """
        import json

        try:
            # Step 1 — Retrieve RAG context
            system_prompt, sources, rag_used = (
                await self._build_prompt(request)
            )

            # Step 2 — Emit RAG metadata event
            rag_event = {
                "type": "rag",
                "content": "",
                "metadata": {
                    "rag_used": rag_used,
                    "sources": sources,
                }
            }
            yield f"data: {json.dumps(rag_event)}\n\n"

            # Step 3 — Stream LLM tokens
            # Wrap in try/except INSIDE the loop
            # to catch errors from the generator itself
            try:
                async for token in self.llm.stream(
                    prompt=request.message,
                    system_prompt=system_prompt,
                ):
                    token_event = {
                        "type": "token",
                        "content": token,
                        "metadata": {},
                    }
                    yield f"data: {json.dumps(token_event)}\n\n"

            except Exception as stream_error:
                logger.error(
                    f"Stream error from LLM: {stream_error}"
                )
                error_event = {
                    "type": "error",
                    "content": str(stream_error),
                    "metadata": {},
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                return   # stop — don't emit done after error

            # Step 4 — Send done sentinel
            done_event = {
                "type": "done",
                "content": "",
                "metadata": {"sources": sources},
            }
            yield f"data: {json.dumps(done_event)}\n\n"

        except Exception as e:
            logger.error(f"Chat stream outer error: {e}")
            error_event = {
                "type": "error",
                "content": str(e),
                "metadata": {},
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    # ── Private helpers ───────────────────────────────────────────

    async def _build_prompt(
        self, request: ChatRequest
    ) -> tuple[str, list[str], bool]:
        """
        Build system prompt with optional RAG context.

        Returns:
            system_prompt: formatted prompt string
            sources: list of source filenames
            rag_used: whether RAG context was found

        Chapter 10: RCT template applied here.
        """
        if not request.use_rag or self.rag is None:
            return SYSTEM_PROMPT_WITHOUT_RAG, [], False

        # Retrieve relevant chunks
        rag_response = await self.rag.query(
            RAGQueryRequest(
                query=request.message,
                limit=request.rag_limit,
                score_threshold=request.rag_score_threshold,
            )
        )

        if not rag_response.results:
            logger.info("No RAG context found — using base prompt")
            return SYSTEM_PROMPT_WITHOUT_RAG, [], False

        # Build prompt with context
        system_prompt = SYSTEM_PROMPT_WITH_RAG.format(
            context=rag_response.context
        )

        sources = list({
            r.filename for r in rag_response.results
        })

        logger.info(
            f"RAG context built | "
            f"chunks={len(rag_response.results)} "
            f"sources={sources}"
        )

        return system_prompt, sources, True
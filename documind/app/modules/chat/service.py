# app/modules/chat/service.py — replace entire file

from loguru import logger
from typing import AsyncGenerator
from app.modules.chat.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    MessageRole,
)
from app.modules.guardrails.pipeline import GuardrailPipeline
from app.modules.rag.pipeline import RAGPipeline
from app.modules.rag.schemas import RAGQueryRequest
from app.providers.llm import MockLLMClient

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
    Orchestrates RAG + guardrails + LLM generation.
    Chapter 9: guardrails wrap every LLM interaction.
    """

    def __init__(
        self,
        llm_client: MockLLMClient,
        rag_pipeline: RAGPipeline | None = None,
        guardrail_pipeline: GuardrailPipeline | None = None,
    ) -> None:
        self.llm = llm_client
        self.rag = rag_pipeline
        self.guardrails = guardrail_pipeline

    async def chat(
        self, request: ChatRequest
    ) -> ChatResponse:
        """Non-streaming chat with guardrails."""

        # Input guardrails
        if self.guardrails:
            input_result = await self.guardrails.check_input(
                request.message
            )
            if not input_result.passed:
                return ChatResponse(
                    message=(
                        "I cannot process this request. "
                        f"{input_result.failure_reason}"
                    ),
                    rag_context_used=False,
                    sources=[],
                )

        system_prompt, sources, rag_used = (
            await self._build_prompt(request)
        )

        response_text = await self.llm.generate(
            prompt=request.message,
            system_prompt=system_prompt,
            temperature=request.temperature,
        )

        # Output guardrails
        if self.guardrails:
            output_result = await self.guardrails.check_output(
                response=response_text,
                context=system_prompt,
            )
            if not output_result.passed:
                return ChatResponse(
                    message=(
                        "I cannot provide this response. "
                        "Please rephrase your question."
                    ),
                    rag_context_used=rag_used,
                    sources=sources,
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
        """SSE streaming chat with guardrails."""
        import json

        try:
            # Input guardrails — check before streaming
            if self.guardrails:
                input_result = (
                    await self.guardrails.check_input(
                        request.message
                    )
                )
                if not input_result.passed:
                    error_event = {
                        "type": "error",
                        "content": (
                            "Request blocked by safety guardrails. "
                            f"{input_result.failure_reason}"
                        ),
                        "metadata": {
                            "blocked_by": input_result.blocked_by
                        },
                    }
                    yield f"data: {json.dumps(error_event)}\n\n"
                    return

            system_prompt, sources, rag_used = (
                await self._build_prompt(request)
            )

            # RAG event
            rag_event = {
                "type": "rag",
                "content": "",
                "metadata": {
                    "rag_used": rag_used,
                    "sources": sources,
                },
            }
            yield f"data: {json.dumps(rag_event)}\n\n"

            # Stream tokens
            full_response = []
            try:
                async for token in self.llm.stream(
                    prompt=request.message,
                    system_prompt=system_prompt,
                ):
                    full_response.append(token)
                    token_event = {
                        "type": "token",
                        "content": token,
                        "metadata": {},
                    }
                    yield f"data: {json.dumps(token_event)}\n\n"

            except Exception as stream_error:
                logger.error(f"Stream error: {stream_error}")
                error_event = {
                    "type": "error",
                    "content": str(stream_error),
                    "metadata": {},
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                return

            # Output guardrails — check after streaming
            if self.guardrails:
                assembled = "".join(full_response)
                output_result = (
                    await self.guardrails.check_output(
                        response=assembled,
                        context=system_prompt,
                    )
                )
                if not output_result.passed:
                    blocked_event = {
                        "type": "error",
                        "content": (
                            "Response blocked by safety guardrails."
                        ),
                        "metadata": {
                            "blocked_by": (
                                output_result.blocked_by
                            )
                        },
                    }
                    yield (
                        f"data: {json.dumps(blocked_event)}\n\n"
                    )
                    return

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

    async def _build_prompt(
        self, request: ChatRequest
    ) -> tuple[str, list[str], bool]:
        """Build system prompt with optional RAG context."""
        if not request.use_rag or self.rag is None:
            return SYSTEM_PROMPT_WITHOUT_RAG, [], False

        rag_response = await self.rag.query(
            RAGQueryRequest(
                query=request.message,
                limit=request.rag_limit,
                score_threshold=request.rag_score_threshold,
            )
        )

        if not rag_response.results:
            return SYSTEM_PROMPT_WITHOUT_RAG, [], False

        system_prompt = SYSTEM_PROMPT_WITH_RAG.format(
            context=rag_response.context
        )
        sources = list({
            r.filename for r in rag_response.results
        })

        return system_prompt, sources, True
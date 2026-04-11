# app/modules/chat/service.py — replace entire file

from loguru import logger
from typing import AsyncGenerator
from app.modules.cache.manager import CacheManager
from app.modules.chat.prompt_builder import (
    build_system_prompt,
    count_tokens,
)
from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
)
from app.modules.chat.structured_output import (
    EnhancedChatResponse,
    TokenUsage,
)
from app.modules.guardrails.pipeline import GuardrailPipeline
from app.modules.rag.pipeline import RAGPipeline
from app.modules.rag.schemas import RAGQueryRequest
from app.providers.llm import MockLLMClient


class ChatService:
    """
    Orchestrates cache → guardrails → RAG → LLM pipeline.

    Chapter 10: cache checked before any LLM call.
    Chapter 9:  guardrails wrap every LLM interaction.
    Chapter 5:  fully async throughout.
    """

    def __init__(
        self,
        llm_client: MockLLMClient,
        rag_pipeline: RAGPipeline | None = None,
        guardrail_pipeline: GuardrailPipeline | None = None,
        cache_manager: CacheManager | None = None,
    ) -> None:
        self.llm = llm_client
        self.rag = rag_pipeline
        self.guardrails = guardrail_pipeline
        self.cache = cache_manager

    async def chat(
        self, request: ChatRequest
    ) -> ChatResponse:
        """Non-streaming chat with full pipeline."""

        # ── Layer 1: Cache lookup ─────────────────────────────
        if self.cache:
            hit = await self.cache.get(request.message)
            if hit:
                return ChatResponse(
                    message=hit.entry.response,
                    rag_context_used=hit.entry.rag_context_used,
                    sources=hit.entry.sources,
                    prompt_tokens=0,
                )

        # ── Layer 2: Input guardrails ─────────────────────────
        if self.guardrails:
            input_result = (
                await self.guardrails.check_input(
                    request.message
                )
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

        # ── Layer 3: RAG + LLM ────────────────────────────────
        system_prompt, sources, rag_used = (
            await self._build_prompt(request)
        )

        response_text = await self.llm.generate(
            prompt=request.message,
            system_prompt=system_prompt,
            temperature=request.temperature,
        )

        # ── Layer 4: Output guardrails ────────────────────────
        if self.guardrails:
            output_result = (
                await self.guardrails.check_output(
                    response=response_text,
                    context=system_prompt,
                )
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

        # ── Layer 5: Store in cache ───────────────────────────
        if self.cache:
            await self.cache.set(
                query=request.message,
                response=response_text,
                sources=sources,
                rag_context_used=rag_used,
            )

        prompt_tokens = count_tokens(
            system_prompt + request.message
        )

        return ChatResponse(
            message=response_text,
            rag_context_used=rag_used,
            sources=sources,
            prompt_tokens=prompt_tokens,
        )

    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """SSE streaming chat with cache + guardrails."""
        import json

        try:
            # ── Cache lookup ──────────────────────────────────
            if self.cache:
                hit = await self.cache.get(request.message)
                if hit:
                    # Emit cache metadata
                    cache_event = {
                        "type": "rag",
                        "content": "",
                        "metadata": {
                            "rag_used": (
                                hit.entry.rag_context_used
                            ),
                            "sources": hit.entry.sources,
                            "cache_hit": True,
                            "cache_type": hit.cache_type,
                            "similarity_score": (
                                hit.similarity_score
                            ),
                        },
                    }
                    yield (
                        f"data: {json.dumps(cache_event)}\n\n"
                    )

                    # Stream cached response token by token
                    words = hit.entry.response.split(" ")
                    for i, word in enumerate(words):
                        token = (
                            word
                            if i == len(words) - 1
                            else f"{word} "
                        )
                        token_event = {
                            "type": "token",
                            "content": token,
                            "metadata": {},
                        }
                        yield (
                            f"data: "
                            f"{json.dumps(token_event)}\n\n"
                        )

                    done_event = {
                        "type": "done",
                        "content": "",
                        "metadata": {
                            "sources": hit.entry.sources,
                            "cache_hit": True,
                        },
                    }
                    yield (
                        f"data: {json.dumps(done_event)}\n\n"
                    )
                    return

            # ── Input guardrails ──────────────────────────────
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
                            "Request blocked by safety "
                            "guardrails. "
                            f"{input_result.failure_reason}"
                        ),
                        "metadata": {
                            "blocked_by": (
                                input_result.blocked_by
                            )
                        },
                    }
                    yield (
                        f"data: {json.dumps(error_event)}\n\n"
                    )
                    return

            system_prompt, sources, rag_used = (
                await self._build_prompt(request)
            )

            # RAG metadata event
            rag_event = {
                "type": "rag",
                "content": "",
                "metadata": {
                    "rag_used": rag_used,
                    "sources": sources,
                    "cache_hit": False,
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
                    yield (
                        f"data: {json.dumps(token_event)}\n\n"
                    )

            except Exception as stream_error:
                logger.error(
                    f"Stream error: {stream_error}"
                )
                error_event = {
                    "type": "error",
                    "content": str(stream_error),
                    "metadata": {},
                }
                yield (
                    f"data: {json.dumps(error_event)}\n\n"
                )
                return

            # Output guardrails
            assembled = "".join(full_response)
            if self.guardrails:
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
                            "Response blocked by safety "
                            "guardrails."
                        ),
                        "metadata": {
                            "blocked_by": (
                                output_result.blocked_by
                            )
                        },
                    }
                    yield (
                        f"data: "
                        f"{json.dumps(blocked_event)}\n\n"
                    )
                    return

            # Store in cache
            if self.cache:
                await self.cache.set(
                    query=request.message,
                    response=assembled,
                    sources=sources,
                    rag_context_used=rag_used,
                )

            done_event = {
                "type": "done",
                "content": "",
                "metadata": {
                    "sources": sources,
                    "cache_hit": False,
                },
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
            return (
                build_system_prompt(context=None),
                [],
                False,
            )

        rag_response = await self.rag.query(
            RAGQueryRequest(
                query=request.message,
                limit=request.rag_limit,
                score_threshold=request.rag_score_threshold,
            )
        )

        if not rag_response.results:
            return (
                build_system_prompt(context=None),
                [],
                False,
            )

        system_prompt = build_system_prompt(
            context=rag_response.context,
            sources=rag_response.results,
        )
        sources = list({
            r.filename for r in rag_response.results
        })

        return system_prompt, sources, True
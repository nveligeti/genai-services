# app/modules/chat/structured_output.py
# Chapter 10: typed LLM response schemas

from typing import Annotated, Optional
from pydantic import BaseModel, Field


class DocumentAnswer(BaseModel):
    """
    Structured LLM response with metadata.
    Chapter 10: typed outputs prevent hallucination misses.
    """
    answer: str = Field(
        description="Direct answer to the question"
    )
    answer_found: bool = Field(
        description="Whether the document contained the answer"
    )
    confidence: Annotated[
        float,
        Field(
            ge=0.0, le=1.0,
            description="Confidence score 0-1"
        ),
    ] = 1.0
    source_document: Optional[str] = Field(
        default=None,
        description="Primary source document name"
    )
    relevant_quote: Optional[str] = Field(
        default=None,
        description="Direct quote supporting the answer"
    )


class TokenUsage(BaseModel):
    """Token usage tracking per request."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    model: str = "mock-gpt"

    @classmethod
    def calculate(
        cls,
        prompt: str,
        response: str,
        model: str = "mock-gpt",
    ) -> "TokenUsage":
        from app.modules.chat.prompt_builder import (
            count_tokens,
            estimate_cost,
        )
        prompt_tokens = count_tokens(prompt)
        completion_tokens = count_tokens(response)
        total = prompt_tokens + completion_tokens
        cost = estimate_cost(
            prompt_tokens, completion_tokens, model
        )
        return cls(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            estimated_cost_usd=cost,
            model=model,
        )


class EnhancedChatResponse(BaseModel):
    """
    Enhanced chat response with caching + token metadata.
    Chapter 10: exposes cache hit info and token usage.
    """
    message: str
    rag_context_used: bool
    sources: list[str] = Field(default_factory=list)
    cache_hit: bool = False
    cache_type: str | None = None   # "keyword"|"semantic"|None
    similarity_score: float | None = None
    token_usage: TokenUsage = Field(
        default_factory=TokenUsage
    )
    prompt_tokens: int = 0
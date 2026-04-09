# app/providers/llm.py
# Chapter 3: Mock LLM using external serving strategy pattern
# Chapter 4: Fully typed inputs and outputs

import asyncio
from typing import AsyncGenerator
from loguru import logger
from app.settings import get_settings


class MockLLMClient:
    """
    Mock LLM client that simulates external model serving.

    Chapter 3: mirrors the external serving strategy —
    your FastAPI app treats this as an I/O-bound dependency
    exactly like a real vLLM or OpenAI API call would be.

    Replaced by real provider clients in later phases.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        logger.info(f"MockLLMClient initialized | model={self.model}")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Simulate a complete (non-streaming) LLM response.
        Chapter 5: async simulates network I/O to external model.
        """
        await asyncio.sleep(0.05)  # simulate network latency

        logger.debug(
            f"MockLLM.generate | "
            f"prompt_length={len(prompt)} | "
            f"temp={temperature or self.temperature}"
        )

        return self._build_response(prompt, system_prompt)

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Simulate a streaming LLM response token by token.
        Chapter 6: async generator for SSE streaming.
        """
        response = self._build_response(prompt, system_prompt)
        words = response.split(" ")

        for i, word in enumerate(words):
            await asyncio.sleep(0.02)  # simulate token generation delay
            # yield word with space, except last word
            yield word if i == len(words) - 1 else f"{word} "

    def _build_response(
        self,
        prompt: str,
        system_prompt: str | None,
    ) -> str:
        """Build a deterministic mock response for testing."""
        base = (
            f"[MockLLM | model={self.model}] "
            f"This is a simulated response to your query."
        )

        # Make response reflect the prompt for testability
        if "hello" in prompt.lower():
            return f"{base} Hello! How can I help you today?"
        if "document" in prompt.lower():
            return (
                f"{base} Based on the uploaded documents, "
                f"here is what I found relevant to your query."
            )
        if "?" in prompt:
            return (
                f"{base} That is a great question. "
                f"Here is a detailed answer based on context."
            )

        return f"{base} Prompt received: '{prompt[:50]}...'"


# ── Singleton factory ──────────────────────────────────────────────

_llm_client: MockLLMClient | None = None


def get_llm_client() -> MockLLMClient:
    """
    Chapter 2: Dependency injection factory.
    Returns singleton MockLLMClient instance.
    Phase 3+: swapped for real provider via settings.llm_provider.
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = MockLLMClient()
    return _llm_client


def reset_llm_client() -> None:
    """
    Reset singleton — used in tests to ensure isolation.
    Chapter 11: prevent shared state between tests.
    """
    global _llm_client
    _llm_client = None
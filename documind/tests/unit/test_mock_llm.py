# tests/unit/test_mock_llm.py
# Chapter 11: unit tests for Mock LLM client (Chapter 3)

import pytest
from app.providers.llm import MockLLMClient, reset_llm_client, get_llm_client


class TestMockLLMClient:

    def setup_method(self):
        """Reset singleton before each test — Chapter 11: isolation."""
        reset_llm_client()

    @pytest.mark.asyncio
    async def test_generate_returns_string(self):
        """MFT — basic: generate must always return a string."""
        client = MockLLMClient()
        result = await client.generate("What is FastAPI?")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_includes_model_name(self):
        """MFT — response must identify itself as mock."""
        client = MockLLMClient()
        result = await client.generate("Hello")
        assert "MockLLM" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("prompt,expected_keyword", [
        ("hello world",              "Hello"),
        ("tell me about the document", "document"),
        ("what is FastAPI?",          "question"),
    ])
    async def test_generate_responds_to_prompt_content(
        self, prompt, expected_keyword
    ):
        """
        IT — response changes correctly based on prompt content.
        Chapter 11: directional expectation test.
        """
        client = MockLLMClient()
        result = await client.generate(prompt)
        assert expected_keyword.lower() in result.lower()

    @pytest.mark.asyncio
    async def test_stream_yields_multiple_chunks(self):
        """
        Chapter 11: streaming test — must yield more than one chunk.
        Chapter 6: async generator behavior verification.
        """
        client = MockLLMClient()
        chunks = []
        async for chunk in client.stream("Tell me about FastAPI"):
            chunks.append(chunk)

        assert len(chunks) > 1  # actually streams, not one block

    @pytest.mark.asyncio
    async def test_stream_reassembled_equals_generate(self):
        """
        IT — streaming and non-streaming must produce same content.
        Chapter 11: invariance test.
        """
        client = MockLLMClient()
        prompt = "What is FastAPI?"

        full_response = await client.generate(prompt)

        streamed_parts = []
        async for chunk in client.stream(prompt):
            streamed_parts.append(chunk)

        streamed_response = "".join(streamed_parts)
        assert streamed_response == full_response

    def test_get_llm_client_returns_singleton(self):
        """Chapter 11: verify singleton pattern."""
        client1 = get_llm_client()
        client2 = get_llm_client()
        assert client1 is client2

    def test_reset_llm_client_clears_singleton(self):
        """Chapter 11: verify reset for test isolation."""
        client1 = get_llm_client()
        reset_llm_client()
        client2 = get_llm_client()
        assert client1 is not client2
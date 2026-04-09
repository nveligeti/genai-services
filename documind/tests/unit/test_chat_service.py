# tests/unit/test_chat_service.py
# Chapter 11: unit tests for ChatService

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.chat.schemas import ChatRequest, MessageRole
from app.modules.chat.service import (
    ChatService,
    SYSTEM_PROMPT_WITH_RAG,
    SYSTEM_PROMPT_WITHOUT_RAG,
)
from app.providers.llm import MockLLMClient


@pytest.fixture
def mock_llm():
    client = MockLLMClient()
    client.generate = AsyncMock(
        return_value="This is a mock response"
    )
    return client


@pytest.fixture
def mock_rag():
    """Stub RAG pipeline."""
    rag = AsyncMock()
    from app.modules.rag.schemas import RAGQueryResponse
    rag.query = AsyncMock(
        return_value=RAGQueryResponse(
            query="test",
            results=[],
            total_results=0,
            context="No relevant context found in documents.",
        )
    )
    return rag


@pytest.fixture
def chat_service(mock_llm, mock_rag):
    return ChatService(
        llm_client=mock_llm,
        rag_pipeline=mock_rag,
    )


class TestChatServicePromptBuilding:

    @pytest.mark.asyncio
    async def test_uses_base_prompt_when_rag_disabled(
        self, mock_llm
    ):
        """
        Unit test — use_rag=False skips RAG retrieval.
        Chapter 11: verify correct prompt selected.
        """
        service = ChatService(
            llm_client=mock_llm,
            rag_pipeline=None,
        )
        request = ChatRequest(
            message="What is FastAPI?",
            use_rag=False,
        )
        prompt, sources, rag_used = (
            await service._build_prompt(request)
        )

        assert rag_used is False
        assert sources == []
        assert prompt == SYSTEM_PROMPT_WITHOUT_RAG

    @pytest.mark.asyncio
    async def test_uses_rag_prompt_when_context_found(
        self, mock_llm, mock_rag
    ):
        """
        Unit test — RAG context injected into prompt.
        Chapter 11: verify RCT template used.
        """
        from app.modules.rag.schemas import (
            RAGQueryResponse, SearchResult
        )
        mock_rag.query = AsyncMock(
            return_value=RAGQueryResponse(
                query="test",
                results=[
                    SearchResult(
                        document_id="doc1",
                        filename="guide.pdf",
                        chunk_index=0,
                        original_text="FastAPI is fast",
                        score=0.9,
                    )
                ],
                total_results=1,
                context="FastAPI is fast",
            )
        )

        service = ChatService(
            llm_client=mock_llm,
            rag_pipeline=mock_rag,
        )
        request = ChatRequest(
            message="What is FastAPI?",
            use_rag=True,
        )
        prompt, sources, rag_used = (
            await service._build_prompt(request)
        )

        assert rag_used is True
        assert "guide.pdf" in sources
        assert "FastAPI is fast" in prompt

    @pytest.mark.asyncio
    async def test_falls_back_to_base_prompt_when_no_rag_results(
        self, mock_llm, mock_rag
    ):
        """
        Boundary test — no RAG results → base prompt.
        Chapter 11: boundary condition.
        """
        service = ChatService(
            llm_client=mock_llm,
            rag_pipeline=mock_rag,
        )
        request = ChatRequest(
            message="obscure question",
            use_rag=True,
        )
        prompt, sources, rag_used = (
            await service._build_prompt(request)
        )

        assert rag_used is False
        assert prompt == SYSTEM_PROMPT_WITHOUT_RAG


class TestChatServiceStream:

    @pytest.mark.asyncio
    async def test_stream_emits_rag_event_first(
        self, chat_service
    ):
        """
        Chapter 11: streaming test — first event must be RAG.
        Chapter 6: event ordering matters for client parsing.
        """
        import json
        request = ChatRequest(message="test")

        events = []
        async for chunk in chat_service.chat_stream(request):
            if chunk.startswith("data: "):
                event = json.loads(chunk[6:])
                events.append(event)

        assert events[0]["type"] == "rag"

    @pytest.mark.asyncio
    async def test_stream_emits_done_event_last(
        self, chat_service
    ):
        """
        Chapter 11: done sentinel must always be last.
        Chapter 6: client relies on done to close connection.
        """
        import json
        request = ChatRequest(message="test")

        events = []
        async for chunk in chat_service.chat_stream(request):
            if chunk.startswith("data: "):
                event = json.loads(chunk[6:])
                events.append(event)

        assert events[-1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_stream_emits_token_events(
        self, chat_service
    ):
        """
        Chapter 11: MFT — tokens must actually stream.
        Not one block — multiple token events.
        """
        import json
        request = ChatRequest(message="Hello")

        token_events = []
        async for chunk in chat_service.chat_stream(request):
            if chunk.startswith("data: "):
                event = json.loads(chunk[6:])
                if event["type"] == "token":
                    token_events.append(event)

        assert len(token_events) > 1

    @pytest.mark.asyncio
    async def test_stream_tokens_reassemble_to_complete_response(
        self, mock_llm
    ):
        """
        IT — streaming tokens must equal full generate response.
        Chapter 11: invariance test.
        Use REAL MockLLMClient (no mocked generate/stream)
        so both methods use the same _build_response logic.
        """
        from app.providers.llm import MockLLMClient
        from app.modules.rag.schemas import RAGQueryResponse

        # Use real MockLLMClient — not the fixture with mocked generate
        real_llm = MockLLMClient()
        mock_rag = AsyncMock()
        mock_rag.query = AsyncMock(
            return_value=RAGQueryResponse(
                query="test",
                results=[],
                total_results=0,
                context="No relevant context found in documents.",
            )
        )

        service = ChatService(
            llm_client=real_llm,
            rag_pipeline=mock_rag,
        )

        request = ChatRequest(
            message="What is FastAPI?",
            use_rag=False,
        )

        # Get full non-streaming response
        full = await service.chat(request)

        # Get streaming tokens
        tokens = []
        async for chunk in service.chat_stream(request):
            if chunk.startswith("data: "):
                import json
                event = json.loads(chunk[6:])
                if event["type"] == "token":
                    tokens.append(event["content"])

        streamed = "".join(tokens)
        assert streamed == full.message

# tests/unit/test_chat_service.py
# Replace test_stream_emits_error_event_on_failure

    @pytest.mark.asyncio
    async def test_stream_emits_error_event_on_failure(
        self, mock_llm
    ):
        """
        Boundary test — LLM failure produces error event.
        Chapter 11: error handling, not crash.
        Chapter 6: graceful stream closure on error.

        Key fix: stream() is an async generator.
        Must replace with async generator that raises,
        NOT AsyncMock(side_effect=...) which returns a coroutine.
        """
        import json

        # Replace stream with async generator that raises
        async def failing_stream(*args, **kwargs):
            raise Exception("LLM unavailable")
            yield  # makes this an async generator

        mock_llm.stream = failing_stream

        service = ChatService(
            llm_client=mock_llm,
            rag_pipeline=None,
        )
        request = ChatRequest(
            message="test", use_rag=False
        )

        events = []
        async for chunk in service.chat_stream(request):
            if chunk.startswith("data: "):
                event = json.loads(chunk[6:])
                events.append(event)

        error_events = [
            e for e in events if e["type"] == "error"
        ]
        assert len(error_events) == 1
        assert "LLM unavailable" in error_events[0]["content"]
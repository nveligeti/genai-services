# tests/unit/test_chat_schemas.py
# Chapter 11: unit tests for chat schemas (Chapter 4)

import pytest
from pydantic import ValidationError
from app.modules.chat.schemas import ChatRequest, ChatMessage, MessageRole


class TestChatRequest:

    def test_valid_request_creates_successfully(self):
        req = ChatRequest(message="What is FastAPI?")
        assert req.message == "What is FastAPI?"
        assert req.use_rag is True
        assert req.conversation_history == []

    def test_empty_message_rejected(self):
        """Chapter 11: boundary — empty string rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_message_too_long_rejected(self):
        """Chapter 11: boundary — max_length=4000."""
        with pytest.raises(ValidationError):
            ChatRequest(message="a" * 4001)

    def test_temperature_boundaries(self):
        """Chapter 11: parametrize boundary values."""
        # Valid boundaries
        ChatRequest(message="hi", temperature=0.0)
        ChatRequest(message="hi", temperature=1.0)

        # Invalid
        with pytest.raises(ValidationError):
            ChatRequest(message="hi", temperature=1.1)
        with pytest.raises(ValidationError):
            ChatRequest(message="hi", temperature=-0.1)

    def test_conversation_history_accepted(self):
        """Chapter 11: valid data — history populated."""
        req = ChatRequest(
            message="follow up",
            conversation_history=[
                ChatMessage(
                    role=MessageRole.USER,
                    content="Hello"
                ),
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content="Hi there"
                ),
            ],
        )
        assert len(req.conversation_history) == 2
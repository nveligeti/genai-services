# tests/unit/test_entities.py
# Chapter 11: unit tests for ORM entities (Chapter 7)

import pytest
from datetime import datetime, timezone
from app.core.entities import (
    ConversationEntity,
    DocumentEntity,
    MessageEntity,
)


class TestDocumentEntity:

    def test_document_entity_defaults(self):
        """Chapter 11: verify ORM defaults."""
        doc = DocumentEntity(
            filename="test.pdf",
            filepath="/uploads/test.pdf",
            size_bytes=1024,
            content_type="application/pdf",
        )
        assert doc.status == "pending"
        assert doc.chunk_count is None
        assert doc.error_message is None

    def test_document_entity_id_is_generated(self):
        """Chapter 11: UUID generated automatically."""
        doc1 = DocumentEntity(
            filename="a.pdf",
            filepath="/a",
            size_bytes=1,
            content_type="application/pdf",
        )
        doc2 = DocumentEntity(
            filename="b.pdf",
            filepath="/b",
            size_bytes=1,
            content_type="application/pdf",
        )
        assert doc1.id != doc2.id


class TestConversationEntity:

    def test_conversation_defaults(self):
        conv = ConversationEntity()
        assert conv.title == "New Conversation"
        assert conv.is_active is True

    def test_conversation_custom_title(self):
        conv = ConversationEntity(title="My Chat")
        assert conv.title == "My Chat"
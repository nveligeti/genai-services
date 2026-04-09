# tests/unit/test_document_schemas.py
# Chapter 11: unit tests for Pydantic schemas (Chapter 4)

import pytest
from pydantic import ValidationError
from app.modules.documents.schemas import (
    DocumentStatus,
    DocumentUploadResponse,
    AllowedContentType,
)
from datetime import datetime


class TestDocumentUploadResponse:

    def test_valid_response_creates_successfully(self):
        response = DocumentUploadResponse(
            document_id="abc123",
            filename="test.pdf",
            status=DocumentStatus.PENDING,
            message="Uploaded",
            size_bytes=1024,
            content_type="application/pdf",
        )
        assert response.document_id == "abc123"
        assert response.status == DocumentStatus.PENDING

    def test_size_kb_computed_field(self):
        """Chapter 4: computed field correctness."""
        response = DocumentUploadResponse(
            document_id="abc123",
            filename="test.pdf",
            status=DocumentStatus.PENDING,
            message="Uploaded",
            size_bytes=2048,
            content_type="application/pdf",
        )
        assert response.size_kb == 2.0

    def test_uploaded_at_defaults_to_now(self):
        """Chapter 4: default_factory sets current time."""
        before = datetime.utcnow()
        response = DocumentUploadResponse(
            document_id="abc123",
            filename="test.pdf",
            status=DocumentStatus.PENDING,
            message="Uploaded",
            size_bytes=1024,
            content_type="application/pdf",
        )
        after = datetime.utcnow()
        assert before <= response.uploaded_at <= after

    @pytest.mark.parametrize("status", list(DocumentStatus))
    def test_all_document_statuses_are_valid(self, status):
        """Chapter 11: parametrize all enum values."""
        response = DocumentUploadResponse(
            document_id="abc123",
            filename="test.pdf",
            status=status,
            message="msg",
            size_bytes=100,
            content_type="application/pdf",
        )
        assert response.status == status
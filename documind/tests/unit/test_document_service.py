# tests/unit/test_document_service.py
# Chapter 11: unit tests with async mocking (Chapter 5)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.documents.service import DocumentService
from app.modules.documents.schemas import DocumentStatus
from app.exceptions import ValidationException


class TestDocumentServiceValidation:
    """Unit tests — mock all I/O, test only validation logic."""

    def test_rejects_unsupported_content_type(self):
        """
        Chapter 11: invalid data boundary test.
        Chapter 4: content type validation.
        """
        service = DocumentService()
        mock_file = MagicMock()
        mock_file.content_type = "video/mp4"  # not allowed
        mock_file.filename = "video.mp4"

        with pytest.raises(ValidationException) as exc_info:
            service._validate_content_type(mock_file)

        assert "Unsupported" in exc_info.value.message
        assert "video/mp4" in exc_info.value.message

    def test_rejects_file_exceeding_size_limit(self):
        """Chapter 11: boundary test — just over the limit."""
        service = DocumentService()
        over_limit = 50 * 1024 * 1024 + 1  # 50MB + 1 byte

        with pytest.raises(ValidationException) as exc_info:
            service._validate_file_size(over_limit)

        assert "too large" in exc_info.value.message.lower()

    def test_accepts_file_at_exact_size_limit(self):
        """Chapter 11: boundary test — exactly at limit must pass."""
        service = DocumentService()
        at_limit = 50 * 1024 * 1024  # exactly 50MB
        # Should NOT raise
        service._validate_file_size(at_limit)

    @pytest.mark.parametrize("filename,expected", [
        ("my document.pdf",    "my_document.pdf"),
        ("../../../etc/passwd", "passwd"),
        ("normal.pdf",         "normal.pdf"),
        ("spaces in name.txt", "spaces_in_name.txt"),
    ])
    def test_filename_sanitization(self, filename, expected):
        """
        Chapter 11: parametrized security boundary tests.
        Path traversal attack prevention.
        """
        service = DocumentService()
        result = service._sanitize_filename(filename)
        assert result == expected


class TestDocumentServiceUpload:

    @pytest.mark.asyncio
    async def test_upload_stores_document_metadata(self, tmp_path, monkeypatch):
        """
        Integration test — verify metadata stored after upload.
        Chapter 11: spy on store to verify side effect.
        """
        monkeypatch.setattr(
            "app.modules.documents.service.UPLOAD_DIR", tmp_path
        )

        # Clear in-memory store between tests
        import app.modules.documents.service as svc_module
        svc_module._document_store.clear()

        service = DocumentService()
        mock_file = AsyncMock()
        mock_file.content_type = "application/pdf"
        mock_file.filename = "test.pdf"
        mock_file.read = AsyncMock(side_effect=[b"PDF content", b""])

        response = await service.save_upload(mock_file)

        assert response.document_id in svc_module._document_store
        assert response.status == DocumentStatus.PENDING
        assert response.filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_extract_text_updates_status_to_ready(
        self, tmp_path, monkeypatch
    ):
        """
        Integration test — verify status lifecycle.
        PENDING → PROCESSING → READY
        Chapter 11: state transition test.
        """
        import app.modules.documents.service as svc_module
        monkeypatch.setattr(
            "app.modules.documents.service.UPLOAD_DIR", tmp_path
        )
        svc_module._document_store.clear()

        # Create a real text file for extraction
        test_file = tmp_path / "doc123_test.txt"
        test_file.write_text("FastAPI is a great framework " * 20)

        doc_id = "doc123"
        svc_module._document_store[doc_id] = {
            "document_id":   doc_id,
            "filename":      "test.txt",
            "filepath":      str(test_file),
            "status":        DocumentStatus.PENDING,
            "size_bytes":    100,
            "content_type":  "text/plain",
            "uploaded_at":   __import__("datetime").datetime.utcnow(),
            "processed_at":  None,
            "error_message": None,
            "chunk_count":   None,
        }

        service = DocumentService()
        await service.extract_text(doc_id)

        updated = svc_module._document_store[doc_id]
        assert updated["status"] == DocumentStatus.READY
        assert updated["chunk_count"] is not None
        assert updated["chunk_count"] > 0
        assert updated["processed_at"] is not None
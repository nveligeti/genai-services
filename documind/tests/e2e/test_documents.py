# tests/e2e/test_documents.py
# Chapter 11: E2E tests for document upload endpoint

import io
import pytest
import asyncio
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def auth(client, registered_user, auth_headers, app):
    """
    Auto-inject auth for all document tests.
    Bypasses CurrentUserDep for existing tests.
    """
    from app.modules.auth.dependencies import get_current_user
    from app.modules.auth.schemas import AuthenticatedUser

    mock_user = AuthenticatedUser(
        user_id="test-user-id",
        email="test@example.com",
        role="USER",
        token_id="test-token-id",
    )
    app.dependency_overrides[get_current_user] = (
        lambda: mock_user
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)

class TestDocumentUploadEndpoint:

    def test_upload_pdf_returns_202(self, client: TestClient):
        """E2E: upload must return 202 Accepted immediately."""
        pdf_content = b"%PDF-1.4 fake pdf content for testing"
        response = client.post(
            "/documents/upload",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == 202

    def test_upload_response_contract(self, client: TestClient):
        """
        E2E: response contract — not exact values.
        Chapter 11: nonbrittle assertion pattern.
        """
        pdf_content = b"%PDF-1.4 fake pdf content for testing"
        response = client.post(
            "/documents/upload",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )
        data = response.json()

        assert "document_id" in data
        assert "filename" in data
        assert "status" in data
        assert "size_bytes" in data
        assert "size_kb" in data       # computed field
        assert "uploaded_at" in data

    def test_upload_initial_status_is_pending(self, client: TestClient):
        """E2E: document must start in PENDING status."""
        pdf_content = b"%PDF-1.4 fake pdf content"
        response = client.post(
            "/documents/upload",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )
        assert response.json()["status"] == "pending"

    def test_upload_rejects_unsupported_type(self, client: TestClient):
        """
        E2E: boundary test — unsupported file type rejected.
        Chapter 11: invalid data test.
        """
        response = client.post(
            "/documents/upload",
            files={"file": ("video.mp4", b"fake video", "video/mp4")},
        )
        assert response.status_code == 422
        assert "Unsupported" in response.json()["detail"]

    def test_upload_txt_file_accepted(self, client: TestClient):
        """E2E: text files must also be accepted."""
        response = client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"plain text content", "text/plain")},
        )
        assert response.status_code == 202

    def test_get_document_after_upload(self, client: TestClient):
        """
        E2E: vertical test — upload then retrieve.
        Chapter 11: tests two endpoints working together.
        """
        # Upload
        pdf_content = b"%PDF-1.4 fake pdf content"
        upload = client.post(
            "/documents/upload",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )
        document_id = upload.json()["document_id"]

        # Retrieve
        get_response = client.get(f"/documents/{document_id}")
        assert get_response.status_code == 200
        assert get_response.json()["document_id"] == document_id

    def test_get_nonexistent_document_returns_404(self, client: TestClient):
        """Chapter 11: boundary test — missing resource."""
        response = client.get("/documents/nonexistent-id-12345")
        assert response.status_code == 404

    def test_list_documents_returns_empty_initially(self, client: TestClient):
        """E2E: list endpoint contract."""
        response = client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)

    def test_uploaded_document_appears_in_list(self, client: TestClient):
        """
        E2E: horizontal test — upload then verify in list.
        Chapter 11: side effect verification.
        """
        # Upload a document
        pdf_content = b"%PDF-1.4 fake pdf content"
        upload = client.post(
            "/documents/upload",
            files={"file": ("listed.pdf", pdf_content, "application/pdf")},
        )
        document_id = upload.json()["document_id"]

        # Check it appears in list
        list_response = client.get("/documents")
        doc_ids = [d["document_id"] for d in list_response.json()["documents"]]
        assert document_id in doc_ids
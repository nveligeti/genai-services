# app/modules/documents/schemas.py
# Chapter 4: Type-safe request/response schemas

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Annotated


class DocumentStatus(str, Enum):
    """Lifecycle states of an uploaded document."""
    PENDING    = "pending"     # uploaded, not yet processed
    PROCESSING = "processing"  # text extraction in progress
    READY      = "ready"       # processed, available for RAG
    FAILED     = "failed"      # processing failed


class AllowedContentType(str, Enum):
    """Supported upload MIME types."""
    PDF  = "application/pdf"
    TEXT = "text/plain"


class DocumentUploadResponse(BaseModel):
    """
    Response returned immediately after upload.
    Processing happens in background (Chapter 5).
    """
    document_id: str
    filename: str
    status: DocumentStatus
    message: str
    size_bytes: int
    content_type: str
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    @computed_field
    @property
    def size_kb(self) -> float:
        """Chapter 4: computed field — derived from size_bytes."""
        return round(self.size_bytes / 1024, 2)


class DocumentStatusResponse(BaseModel):
    """Response for status check endpoint."""
    document_id: str
    filename: str
    status: DocumentStatus
    size_bytes: int
    content_type: str
    uploaded_at: datetime
    processed_at: datetime | None = None
    error_message: str | None = None
    chunk_count: int | None = None


class DocumentListResponse(BaseModel):
    """Paginated list of uploaded documents."""
    documents: list[DocumentStatusResponse]
    total: int
    skip: int
    take: int
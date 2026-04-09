# app/modules/documents/service.py
# Chapter 5: Async file I/O + background task logic

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

import aiofiles
import aiofiles.os
from fastapi import UploadFile
from loguru import logger
from pypdf import PdfReader

from app.modules.documents.schemas import (
    AllowedContentType,
    DocumentStatus,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.exceptions import ValidationException, NotFoundException

# In-memory store for Phase 2
# Replaced by Postgres in Phase 5
_document_store: dict[str, dict] = {}

UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MB read chunks


class DocumentService:
    """
    Handles document upload, storage, and text extraction.

    Chapter 3: uses background task pattern for heavy processing
    Chapter 5: async file I/O throughout
    Chapter 4: all inputs/outputs are Pydantic validated
    """

    async def save_upload(self, file: UploadFile) -> DocumentUploadResponse:
        """
        Asynchronously save an uploaded file to disk.
        Returns immediately — processing happens in background.
        Chapter 5: async chunked file writing.
        """
        self._validate_content_type(file)

        await aiofiles.os.makedirs(UPLOAD_DIR, exist_ok=True)

        document_id = uuid.uuid4().hex
        safe_filename = self._sanitize_filename(file.filename or "upload")
        filepath = UPLOAD_DIR / f"{document_id}_{safe_filename}"

        size_bytes = await self._write_file(file, filepath)

        self._validate_file_size(size_bytes)

        # Store metadata in memory (Phase 5: moves to Postgres)
        _document_store[document_id] = {
            "document_id":   document_id,
            "filename":      safe_filename,
            "filepath":      str(filepath),
            "status":        DocumentStatus.PENDING,
            "size_bytes":    size_bytes,
            "content_type":  file.content_type,
            "uploaded_at":   datetime.utcnow(),
            "processed_at":  None,
            "error_message": None,
            "chunk_count":   None,
        }

        logger.info(
            f"Document uploaded | id={document_id} "
            f"file={safe_filename} size={size_bytes}b"
        )

        return DocumentUploadResponse(
            document_id=document_id,
            filename=safe_filename,
            status=DocumentStatus.PENDING,
            message="Document uploaded. Processing started in background.",
            size_bytes=size_bytes,
            content_type=file.content_type or "application/octet-stream",
        )

    async def extract_text(self, document_id: str) -> None:
        """
        Extract text from uploaded document.
        Runs as a background task (Chapter 5).
        Updates document status throughout.
        """
        doc = _document_store.get(document_id)
        if not doc:
            logger.error(f"Document not found for extraction: {document_id}")
            return

        self._update_status(document_id, DocumentStatus.PROCESSING)
        logger.info(f"Starting text extraction | id={document_id}")

        try:
            filepath = Path(doc["filepath"])
            content_type = doc["content_type"]

            if content_type == AllowedContentType.PDF:
                text = await self._extract_pdf_text(filepath)
            else:
                text = await self._read_text_file(filepath)

            # Write extracted text alongside original file
            text_filepath = filepath.with_suffix(".txt")
            async with aiofiles.open(
                text_filepath, "w", encoding="utf-8"
            ) as f:
                await f.write(text)

            # Count rough chunks (512 char chunks for Phase 3)
            chunk_count = max(1, len(text) // 512)

            self._update_status(
                document_id,
                DocumentStatus.READY,
                chunk_count=chunk_count,
            )

            logger.info(
                f"Text extraction complete | id={document_id} "
                f"chunks={chunk_count}"
            )

        except Exception as e:
            logger.error(
                f"Text extraction failed | id={document_id} | error={e}"
            )
            self._update_status(
                document_id,
                DocumentStatus.FAILED,
                error_message=str(e),
            )

    def get_document(self, document_id: str) -> DocumentStatusResponse:
        """Retrieve document metadata by ID."""
        doc = _document_store.get(document_id)
        if not doc:
            raise NotFoundException("Document", document_id)
        return DocumentStatusResponse(**doc)

    def list_documents(
        self, skip: int = 0, take: int = 20
    ) -> list[DocumentStatusResponse]:
        """Return paginated list of all documents."""
        all_docs = list(_document_store.values())
        paginated = all_docs[skip: skip + take]
        return [DocumentStatusResponse(**d) for d in paginated]

    # ── Private helpers ───────────────────────────────────────────

    def _validate_content_type(self, file: UploadFile) -> None:
        """Chapter 4: input validation — reject unsupported types."""
        allowed = {ct.value for ct in AllowedContentType}
        if file.content_type not in allowed:
            raise ValidationException(
                f"Unsupported file type '{file.content_type}'. "
                f"Allowed: {', '.join(allowed)}"
            )

    def _validate_file_size(self, size_bytes: int) -> None:
        """Chapter 4: input validation — reject oversized files."""
        if size_bytes > MAX_FILE_SIZE_BYTES:
            raise ValidationException(
                f"File too large ({size_bytes / 1024 / 1024:.1f} MB). "
                f"Maximum allowed: {MAX_FILE_SIZE_MB} MB"
            )

    def _sanitize_filename(self, filename: str) -> str:
        """Prevent path traversal attacks."""
        return Path(filename).name.replace(" ", "_")

    async def _write_file(
        self, file: UploadFile, filepath: Path
    ) -> int:
        """
        Write uploaded file to disk in chunks.
        Chapter 5: chunked async write prevents memory exhaustion.
        """
        size_bytes = 0
        async with aiofiles.open(filepath, "wb") as f:
            while chunk := await file.read(DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
                size_bytes += len(chunk)
        return size_bytes

    async def _extract_pdf_text(self, filepath: Path) -> str:
        """
        Extract text from PDF.
        pypdf is synchronous — runs in thread pool via asyncio.
        Chapter 5: avoid blocking event loop with CPU-bound ops.
        """
        import asyncio

        def _sync_extract() -> str:
            reader = PdfReader(str(filepath), strict=False)
            content = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    content += f"{page_text}\n\n"
            return content

        # Run sync PDF extraction in thread pool
        # so it doesn't block the async event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_extract)

    async def _read_text_file(self, filepath: Path) -> str:
        """Async read for plain text files."""
        async with aiofiles.open(
            filepath, "r", encoding="utf-8", errors="replace"
        ) as f:
            return await f.read()

    def _update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        **kwargs,
    ) -> None:
        """Update document metadata in store."""
        if document_id in _document_store:
            _document_store[document_id]["status"] = status
            if status == DocumentStatus.READY:
                _document_store[document_id]["processed_at"] = (
                    datetime.utcnow()
                )
            _document_store[document_id].update(kwargs)
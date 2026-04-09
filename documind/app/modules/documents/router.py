# app/modules/documents/router.py
# Chapter 2: Modular router
# Chapter 5: BackgroundTasks for async processing

from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from app.modules.documents.schemas import (
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.modules.documents.service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service() -> DocumentService:
    """
    Chapter 2: Dependency injection for DocumentService.
    Replaced with DB-backed version in Phase 5.
    """
    return DocumentService()


DocumentServiceDep = Annotated[
    DocumentService, Depends(get_document_service)
]


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=202,  # Accepted — processing in background
    summary="Upload a document for RAG processing",
)
async def upload_document_controller(
    file: Annotated[UploadFile, File(description="PDF or text file")],
    background_tasks: BackgroundTasks,
    service: DocumentServiceDep,
) -> DocumentUploadResponse:
    """
    Upload a document and start background processing.

    Chapter 5: file upload + BackgroundTasks pattern.
    Returns 202 Accepted immediately.
    Processing status tracked via GET /documents/{id}.
    """
    response = await service.save_upload(file)

    # Kick off text extraction in background
    # Chapter 5: non-blocking background task
    background_tasks.add_task(
        service.extract_text,
        response.document_id,
    )

    return response


@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
    summary="Get document processing status",
)
async def get_document_controller(
    document_id: str,
    service: DocumentServiceDep,
) -> DocumentStatusResponse:
    """
    Poll document processing status.
    Chapter 6: used by client to check background task progress.
    """
    return service.get_document(document_id)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded documents",
)
async def list_documents_controller(
    service: DocumentServiceDep,
    skip: int = 0,
    take: int = 20,
) -> DocumentListResponse:
    """Paginated list of all uploaded documents."""
    documents = service.list_documents(skip=skip, take=take)
    return DocumentListResponse(
        documents=documents,
        total=len(documents),
        skip=skip,
        take=take,
    )
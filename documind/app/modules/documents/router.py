# app/modules/documents/router.py — replace entire file

from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from app.modules.auth.dependencies import CurrentUserDep
from app.modules.documents.schemas import (
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.modules.documents.service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service() -> DocumentService:
    return DocumentService()


DocumentServiceDep = Annotated[
    DocumentService, Depends(get_document_service)
]


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=202,
)
async def upload_document_controller(
    file: Annotated[UploadFile, File()],
    background_tasks: BackgroundTasks,
    service: DocumentServiceDep,
    current_user: CurrentUserDep,        # ← protected
) -> DocumentUploadResponse:
    response = await service.save_upload(file)
    background_tasks.add_task(
        service.extract_text,
        response.document_id,
    )
    return response


@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
)
async def get_document_controller(
    document_id: str,
    service: DocumentServiceDep,
    current_user: CurrentUserDep,        # ← protected
) -> DocumentStatusResponse:
    return service.get_document(document_id)


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents_controller(
    service: DocumentServiceDep,
    current_user: CurrentUserDep,        # ← protected
    skip: int = 0,
    take: int = 20,
) -> DocumentListResponse:
    documents = service.list_documents(skip=skip, take=take)
    return DocumentListResponse(
        documents=documents,
        total=len(documents),
        skip=skip,
        take=take,
    )
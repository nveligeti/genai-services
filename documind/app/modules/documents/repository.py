# app/modules/documents/repository.py — replace entire file

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.entities import DocumentEntity
from app.modules.documents.schemas import DocumentStatus


class DocumentRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, entity: DocumentEntity
    ) -> DocumentEntity:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get(
        self, document_id: str
    ) -> Optional[DocumentEntity]:
        result = await self.session.execute(
            select(DocumentEntity).where(
                DocumentEntity.id == document_id
            )
        )
        return result.scalars().first()

    async def list(
        self, skip: int = 0, take: int = 20
    ) -> list[DocumentEntity]:
        result = await self.session.execute(
            select(DocumentEntity)
            .order_by(DocumentEntity.uploaded_at.desc())
            .offset(skip)
            .limit(take)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        **kwargs,
    ) -> None:
        doc = await self.get(document_id)
        if not doc:
            return
        doc.status = status.value
        if status == DocumentStatus.READY:
            doc.processed_at = datetime.now(timezone.utc)
        for key, value in kwargs.items():
            setattr(doc, key, value)
        await self.session.flush()
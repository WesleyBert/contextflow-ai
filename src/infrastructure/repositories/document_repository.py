from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.document import Document, DocumentStatus
from src.domain.repositories.document_repository import DocumentOrderBy, DocumentProcessingStats
from src.infrastructure.database.models.document import DocumentModel

_ORDER_COLUMNS: dict[DocumentOrderBy, ColumnElement[Any]] = {
    "created_at_desc": DocumentModel.created_at.desc(),
    "created_at_asc": DocumentModel.created_at.asc(),
    "filename_asc": DocumentModel.filename.asc(),
    "filename_desc": DocumentModel.filename.desc(),
}


def _to_entity(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        owner_id=model.owner_id,
        filename=model.filename,
        content_type=model.content_type,
        size_bytes=model.size_bytes,
        storage_path=model.storage_path,
        status=model.status,  # type: ignore[arg-type]
        created_at=model.created_at,
        processing_started_at=model.processing_started_at,
        processing_finished_at=model.processing_finished_at,
    )


class SqlAlchemyDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        owner_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
    ) -> Document:
        model = DocumentModel(
            owner_id=owner_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, document_id: UUID) -> Document | None:
        model = await self._session.get(DocumentModel, document_id)
        return _to_entity(model) if model else None

    async def list_by_owner(
        self,
        owner_id: UUID,
        *,
        status: DocumentStatus | None = None,
        search: str | None = None,
        order_by: DocumentOrderBy = "created_at_desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Document], int]:
        filters = [DocumentModel.owner_id == owner_id]
        if status is not None:
            filters.append(DocumentModel.status == status)
        if search:
            filters.append(DocumentModel.filename.ilike(f"%{search}%"))

        total = await self._session.scalar(
            select(func.count()).select_from(DocumentModel).where(*filters)
        )

        result = await self._session.execute(
            select(DocumentModel)
            .where(*filters)
            .order_by(_ORDER_COLUMNS[order_by])
            .limit(limit)
            .offset(offset)
        )
        documents = [_to_entity(model) for model in result.scalars().all()]
        return documents, total or 0

    async def delete(self, document_id: UUID) -> None:
        model = await self._session.get(DocumentModel, document_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()

    async def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        *,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        model = await self._session.get(DocumentModel, document_id)
        if model is not None:
            model.status = status
            if started_at is not None:
                model.processing_started_at = started_at
            if finished_at is not None:
                model.processing_finished_at = finished_at
            await self._session.commit()

    async def processing_stats(self) -> DocumentProcessingStats:
        total = await self._session.scalar(select(func.count()).select_from(DocumentModel))
        ready = await self._session.scalar(
            select(func.count()).select_from(DocumentModel).where(DocumentModel.status == "ready")
        )
        failed = await self._session.scalar(
            select(func.count())
            .select_from(DocumentModel)
            .where(DocumentModel.status == "failed")
        )
        avg_seconds = await self._session.scalar(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        DocumentModel.processing_finished_at - DocumentModel.processing_started_at,
                    )
                )
            ).where(DocumentModel.status == "ready")
        )
        avg_processing_time_ms = round(avg_seconds * 1000, 2) if avg_seconds is not None else None
        return DocumentProcessingStats(
            total=total or 0,
            ready=ready or 0,
            failed=failed or 0,
            avg_processing_time_ms=avg_processing_time_ms,
        )

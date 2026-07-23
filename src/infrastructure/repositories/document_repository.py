from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.document import Document
from src.infrastructure.database.models.document import DocumentModel


def _to_entity(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        owner_id=model.owner_id,
        filename=model.filename,
        content_type=model.content_type,
        size_bytes=model.size_bytes,
        storage_path=model.storage_path,
        created_at=model.created_at,
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

    async def list_by_owner(self, owner_id: UUID) -> list[Document]:
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.owner_id == owner_id)
            .order_by(DocumentModel.created_at.desc())
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def delete(self, document_id: UUID) -> None:
        model = await self._session.get(DocumentModel, document_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()

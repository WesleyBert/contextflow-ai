from uuid import UUID

from src.domain.entities.document import Document
from src.domain.exceptions.base import ForbiddenError, NotFoundError, ValidationError
from src.domain.repositories.document_repository import DocumentRepository
from src.infrastructure.config import get_settings
from src.infrastructure.storage.local_storage import LocalFileStorage


class DocumentService:
    def __init__(self, document_repository: DocumentRepository, storage: LocalFileStorage) -> None:
        self._documents = document_repository
        self._storage = storage

    async def upload_document(
        self, owner_id: UUID, filename: str, content_type: str, content: bytes
    ) -> Document:
        settings = get_settings()

        if content_type not in settings.allowed_upload_content_types:
            raise ValidationError(f"Tipo de arquivo não suportado: {content_type}")
        if len(content) > settings.max_upload_size_bytes:
            raise ValidationError("Arquivo excede o tamanho máximo permitido")

        storage_path = self._storage.save(owner_id, filename, content)

        return await self._documents.create(
            owner_id=owner_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(content),
            storage_path=storage_path,
        )

    async def list_documents(self, owner_id: UUID) -> list[Document]:
        return await self._documents.list_by_owner(owner_id)

    async def get_document(self, owner_id: UUID, document_id: UUID) -> Document:
        document = await self._documents.get_by_id(document_id)
        if document is None:
            raise NotFoundError("Documento não encontrado")
        if document.owner_id != owner_id:
            raise ForbiddenError("Você não tem acesso a este documento")
        return document

    async def delete_document(self, owner_id: UUID, document_id: UUID) -> None:
        document = await self.get_document(owner_id, document_id)
        self._storage.delete(document.storage_path)
        await self._documents.delete(document.id)

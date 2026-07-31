from typing import Literal, Protocol
from uuid import UUID

from src.domain.entities.document import Document, DocumentStatus

DocumentOrderBy = Literal["created_at_desc", "created_at_asc", "filename_asc", "filename_desc"]


class DocumentRepository(Protocol):
    async def create(
        self,
        owner_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
    ) -> Document: ...

    async def get_by_id(self, document_id: UUID) -> Document | None: ...

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
        """Devolve (documentos da página, total de documentos que casam com o filtro)."""
        ...

    async def delete(self, document_id: UUID) -> None: ...

    async def update_status(self, document_id: UUID, status: DocumentStatus) -> None: ...

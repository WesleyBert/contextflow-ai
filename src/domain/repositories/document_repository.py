from typing import Protocol
from uuid import UUID

from src.domain.entities.document import Document


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

    async def list_by_owner(self, owner_id: UUID) -> list[Document]: ...

    async def delete(self, document_id: UUID) -> None: ...

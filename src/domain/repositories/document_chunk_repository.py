from typing import Protocol
from uuid import UUID

from src.domain.entities.document_chunk import DocumentChunk, RetrievedChunk


class DocumentChunkRepository(Protocol):
    async def create_many(
        self, document_id: UUID, owner_id: UUID, chunks: list[str], embeddings: list[list[float]]
    ) -> list[DocumentChunk]: ...

    async def search_similar(
        self, owner_id: UUID, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]: ...

    async def delete_by_document(self, document_id: UUID) -> None: ...

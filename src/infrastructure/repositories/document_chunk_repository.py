from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.document_chunk import DocumentChunk, RetrievedChunk
from src.infrastructure.database.models.document import DocumentModel
from src.infrastructure.database.models.document_chunk import DocumentChunkModel


def _to_entity(model: DocumentChunkModel) -> DocumentChunk:
    return DocumentChunk(
        id=model.id,
        document_id=model.document_id,
        owner_id=model.owner_id,
        chunk_index=model.chunk_index,
        content=model.content,
        embedding=list(model.embedding),
        created_at=model.created_at,
    )


class SqlAlchemyDocumentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(
        self, document_id: UUID, owner_id: UUID, chunks: list[str], embeddings: list[list[float]]
    ) -> list[DocumentChunk]:
        models = [
            DocumentChunkModel(
                document_id=document_id,
                owner_id=owner_id,
                chunk_index=index,
                content=content,
                embedding=embedding,
            )
            for index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True))
        ]
        self._session.add_all(models)
        await self._session.commit()
        return [_to_entity(model) for model in models]

    async def search_similar(
        self, owner_id: UUID, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        distance = DocumentChunkModel.embedding.cosine_distance(query_embedding)
        result = await self._session.execute(
            select(DocumentChunkModel, DocumentModel.filename, distance.label("distance"))
            .join(DocumentModel, DocumentModel.id == DocumentChunkModel.document_id)
            .where(DocumentChunkModel.owner_id == owner_id)
            .order_by(distance)
            .limit(top_k)
        )
        return [
            RetrievedChunk(
                chunk=_to_entity(chunk_model),
                document_filename=filename,
                similarity=1 - dist,
            )
            for chunk_model, filename, dist in result.all()
        ]

    async def delete_by_document(self, document_id: UUID) -> None:
        result = await self._session.execute(
            select(DocumentChunkModel).where(DocumentChunkModel.document_id == document_id)
        )
        for model in result.scalars().all():
            await self._session.delete(model)
        await self._session.commit()

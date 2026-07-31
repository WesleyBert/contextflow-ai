from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.document import Document
from src.infrastructure.repositories.document_chunk_repository import (
    SqlAlchemyDocumentChunkRepository,
)
from src.infrastructure.repositories.document_repository import SqlAlchemyDocumentRepository
from tests.conftest import create_test_user
from tests.fakes import FakeEmbeddingClient


async def _create_document(db_session: AsyncSession, owner_id: UUID, filename: str) -> Document:
    return await SqlAlchemyDocumentRepository(db_session).create(
        owner_id=owner_id,
        filename=filename,
        content_type="text/plain",
        size_bytes=1,
        storage_path=f"/uploads/{filename}",
    )


async def test_create_many_persists_chunks_with_embeddings(db_session: AsyncSession) -> None:
    owner_id = await create_test_user(db_session)
    document = await _create_document(db_session, owner_id, "doc.txt")
    embedding_client = FakeEmbeddingClient(dimensions=768)
    chunk_repository = SqlAlchemyDocumentChunkRepository(db_session)
    texts = ["primeiro trecho", "segundo trecho"]
    embeddings = await embedding_client.embed(texts)

    created = await chunk_repository.create_many(document.id, owner_id, texts, embeddings)

    assert [c.content for c in created] == texts
    assert [c.chunk_index for c in created] == [0, 1]


async def test_search_similar_ranks_by_closest_embedding(db_session: AsyncSession) -> None:
    owner_id = await create_test_user(db_session)
    document = await _create_document(db_session, owner_id, "doc.txt")
    embedding_client = FakeEmbeddingClient(dimensions=768)
    chunk_repository = SqlAlchemyDocumentChunkRepository(db_session)
    texts = ["gatos são animais domésticos", "o clima hoje está ensolarado"]
    embeddings = await embedding_client.embed(texts)
    await chunk_repository.create_many(document.id, owner_id, texts, embeddings)

    [query_embedding] = await embedding_client.embed(["gatos são animais domésticos"])
    results = await chunk_repository.search_similar(owner_id, query_embedding, top_k=5)

    assert results[0].chunk.content == "gatos são animais domésticos"
    assert results[0].document_filename == "doc.txt"


async def test_search_similar_scoped_by_owner(db_session: AsyncSession) -> None:
    owner_a = await create_test_user(db_session)
    owner_b = await create_test_user(db_session)
    document = await _create_document(db_session, owner_a, "doc.txt")
    embedding_client = FakeEmbeddingClient(dimensions=768)
    chunk_repository = SqlAlchemyDocumentChunkRepository(db_session)
    [embedding] = await embedding_client.embed(["texto do owner a"])
    await chunk_repository.create_many(document.id, owner_a, ["texto do owner a"], [embedding])

    results = await chunk_repository.search_similar(owner_b, embedding, top_k=5)

    assert results == []


async def test_delete_by_document_removes_its_chunks(db_session: AsyncSession) -> None:
    owner_id = await create_test_user(db_session)
    document = await _create_document(db_session, owner_id, "doc.txt")
    embedding_client = FakeEmbeddingClient(dimensions=768)
    chunk_repository = SqlAlchemyDocumentChunkRepository(db_session)
    [embedding] = await embedding_client.embed(["algum trecho"])
    await chunk_repository.create_many(document.id, owner_id, ["algum trecho"], [embedding])

    await chunk_repository.delete_by_document(document.id)

    results = await chunk_repository.search_similar(owner_id, embedding, top_k=5)
    assert results == []

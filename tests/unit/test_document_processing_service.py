from datetime import UTC, datetime
from uuid import uuid4

from src.application.services.document_processing_service import DocumentProcessingService
from src.domain.entities.document import Document
from tests.fakes import FakeEmbeddingClient
from tests.unit.repo_fakes import FakeDocumentChunkRepository


def _make_document(content_type: str = "text/plain") -> Document:
    return Document(
        id=uuid4(),
        owner_id=uuid4(),
        filename="doc.txt",
        content_type=content_type,
        size_bytes=100,
        storage_path="/uploads/doc.txt",
        status="processing",
        created_at=datetime.now(UTC),
    )


async def test_process_chunks_and_embeds_text_content() -> None:
    chunk_repository = FakeDocumentChunkRepository()
    embedding_client = FakeEmbeddingClient(dimensions=8)
    service = DocumentProcessingService(chunk_repository, embedding_client)
    document = _make_document()
    content = ("Este é um documento de teste. " * 10).encode("utf-8")

    await service.process(document, content)

    assert len(chunk_repository.create_many_calls) == 1
    _, _, chunks, embeddings = chunk_repository.create_many_calls[0]
    assert len(chunks) > 0
    assert len(embeddings) == len(chunks)
    assert embedding_client.calls == [chunks]


async def test_process_does_nothing_when_no_text_is_extracted() -> None:
    chunk_repository = FakeDocumentChunkRepository()
    embedding_client = FakeEmbeddingClient(dimensions=8)
    service = DocumentProcessingService(chunk_repository, embedding_client)
    document = _make_document()

    await service.process(document, b"   ")

    assert chunk_repository.create_many_calls == []
    assert embedding_client.calls == []


async def test_delete_chunks_delegates_to_repository() -> None:
    chunk_repository = FakeDocumentChunkRepository()
    embedding_client = FakeEmbeddingClient(dimensions=8)
    service = DocumentProcessingService(chunk_repository, embedding_client)
    document_id = uuid4()

    await service.delete_chunks(document_id)

    assert chunk_repository.deleted_document_ids == [document_id]

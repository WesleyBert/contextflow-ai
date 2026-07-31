from unittest.mock import create_autospec
from uuid import UUID, uuid4

import pytest

from src.application.services.document_processing_service import DocumentProcessingService
from src.application.services.document_service import DocumentService
from src.domain.exceptions.base import ForbiddenError, NotFoundError, ValidationError
from src.infrastructure.storage.local_storage import LocalFileStorage
from tests.unit.repo_fakes import FakeDocumentRepository


class FakeTaskQueue:
    def __init__(self) -> None:
        self.enqueued: list[UUID] = []

    def enqueue_document_processing(self, document_id: UUID) -> None:
        self.enqueued.append(document_id)


@pytest.fixture
def storage() -> LocalFileStorage:
    mock = create_autospec(LocalFileStorage, instance=True)
    mock.save.return_value = "/uploads/fake-path.txt"
    return mock


@pytest.fixture
def processing_service() -> DocumentProcessingService:
    return create_autospec(DocumentProcessingService, instance=True)


@pytest.fixture
def task_queue() -> FakeTaskQueue:
    return FakeTaskQueue()


@pytest.fixture
def document_repository() -> FakeDocumentRepository:
    return FakeDocumentRepository()


@pytest.fixture
def document_service(
    document_repository: FakeDocumentRepository,
    storage: LocalFileStorage,
    processing_service: DocumentProcessingService,
    task_queue: FakeTaskQueue,
) -> DocumentService:
    return DocumentService(document_repository, storage, processing_service, task_queue)


async def test_upload_document_rejects_unsupported_content_type(
    document_service: DocumentService, storage: LocalFileStorage
) -> None:
    with pytest.raises(ValidationError):
        await document_service.upload_document(
            owner_id=uuid4(),
            filename="malware.exe",
            content_type="application/x-msdownload",
            content=b"conteudo",
        )

    storage.save.assert_not_called()  # type: ignore[attr-defined]


async def test_upload_document_rejects_file_too_large(document_service: DocumentService) -> None:
    huge_content = b"x" * (25 * 1024 * 1024)

    with pytest.raises(ValidationError):
        await document_service.upload_document(
            owner_id=uuid4(),
            filename="grande.txt",
            content_type="text/plain",
            content=huge_content,
        )


async def test_upload_document_saves_and_enqueues_processing(
    document_service: DocumentService,
    storage: LocalFileStorage,
    processing_service: DocumentProcessingService,
    task_queue: FakeTaskQueue,
) -> None:
    owner_id = uuid4()

    document = await document_service.upload_document(
        owner_id=owner_id, filename="doc.txt", content_type="text/plain", content=b"conteudo"
    )

    storage.save.assert_called_once()  # type: ignore[attr-defined]
    assert document.status == "pending"
    assert task_queue.enqueued == [document.id]
    processing_service.process.assert_not_called()  # type: ignore[attr-defined]


async def test_get_document_raises_not_found(document_service: DocumentService) -> None:
    with pytest.raises(NotFoundError):
        await document_service.get_document(uuid4(), uuid4())


async def test_get_document_raises_forbidden_for_other_owner(
    document_service: DocumentService,
) -> None:
    document = await document_service.upload_document(
        owner_id=uuid4(), filename="doc.txt", content_type="text/plain", content=b"conteudo"
    )

    with pytest.raises(ForbiddenError):
        await document_service.get_document(uuid4(), document.id)


async def test_list_documents_returns_only_owner_documents(
    document_service: DocumentService,
) -> None:
    owner_id = uuid4()
    await document_service.upload_document(
        owner_id=owner_id, filename="meu.txt", content_type="text/plain", content=b"a"
    )
    await document_service.upload_document(
        owner_id=uuid4(), filename="de-outro.txt", content_type="text/plain", content=b"b"
    )

    documents, total = await document_service.list_documents(owner_id)

    assert [d.filename for d in documents] == ["meu.txt"]
    assert total == 1


async def test_delete_document_removes_chunks_file_and_record(
    document_service: DocumentService,
    document_repository: FakeDocumentRepository,
    storage: LocalFileStorage,
    processing_service: DocumentProcessingService,
) -> None:
    owner_id = uuid4()
    document = await document_service.upload_document(
        owner_id=owner_id, filename="doc.txt", content_type="text/plain", content=b"conteudo"
    )

    await document_service.delete_document(owner_id, document.id)

    processing_service.delete_chunks.assert_called_once_with(document.id)  # type: ignore[attr-defined]
    storage.delete.assert_called_once_with(document.storage_path)  # type: ignore[attr-defined]
    assert await document_repository.get_by_id(document.id) is None


async def test_delete_document_raises_forbidden_for_other_owner(
    document_service: DocumentService,
) -> None:
    document = await document_service.upload_document(
        owner_id=uuid4(), filename="doc.txt", content_type="text/plain", content=b"conteudo"
    )

    with pytest.raises(ForbiddenError):
        await document_service.delete_document(uuid4(), document.id)

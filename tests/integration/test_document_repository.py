from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.document_repository import SqlAlchemyDocumentRepository
from tests.conftest import create_test_user


async def test_create_persists_document_with_pending_status(db_session: AsyncSession) -> None:
    repository = SqlAlchemyDocumentRepository(db_session)
    owner_id = await create_test_user(db_session)

    document = await repository.create(
        owner_id=owner_id,
        filename="doc.txt",
        content_type="text/plain",
        size_bytes=10,
        storage_path="/uploads/doc.txt",
    )

    assert document.status == "pending"
    assert document.id is not None
    assert document.created_at is not None


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repository = SqlAlchemyDocumentRepository(db_session)

    assert await repository.get_by_id(uuid4()) is None


async def test_update_status_persists_new_status(db_session: AsyncSession) -> None:
    repository = SqlAlchemyDocumentRepository(db_session)
    owner_id = await create_test_user(db_session)
    document = await repository.create(
        owner_id=owner_id,
        filename="doc.txt",
        content_type="text/plain",
        size_bytes=10,
        storage_path="/uploads/doc.txt",
    )

    await repository.update_status(document.id, "processing")

    updated = await repository.get_by_id(document.id)
    assert updated is not None
    assert updated.status == "processing"


async def test_list_by_owner_returns_only_owner_documents(db_session: AsyncSession) -> None:
    repository = SqlAlchemyDocumentRepository(db_session)
    owner_id = await create_test_user(db_session)
    other_owner_id = await create_test_user(db_session)
    await repository.create(
        owner_id=owner_id,
        filename="meu.txt",
        content_type="text/plain",
        size_bytes=1,
        storage_path="/uploads/meu.txt",
    )
    await repository.create(
        owner_id=other_owner_id,
        filename="de-outro.txt",
        content_type="text/plain",
        size_bytes=1,
        storage_path="/uploads/de-outro.txt",
    )

    documents = await repository.list_by_owner(owner_id)

    assert [d.filename for d in documents] == ["meu.txt"]


async def test_delete_removes_document(db_session: AsyncSession) -> None:
    repository = SqlAlchemyDocumentRepository(db_session)
    owner_id = await create_test_user(db_session)
    document = await repository.create(
        owner_id=owner_id,
        filename="doc.txt",
        content_type="text/plain",
        size_bytes=1,
        storage_path="/uploads/doc.txt",
    )

    await repository.delete(document.id)

    assert await repository.get_by_id(document.id) is None

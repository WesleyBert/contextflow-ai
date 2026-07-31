"""Regressão do bug corrigido em `infrastructure/queue/tasks.py`: o `engine` assíncrono
do SQLAlchemy é um singleton compartilhado com a API, e cada chamada da task Celery roda
`asyncio.run()` (loop novo a cada vez). Sem o `engine.dispose()` no fim de cada execução,
a segunda chamada em diante reusava uma conexão do pool presa ao loop já fechado da
chamada anterior e quebrava com `AttributeError` dentro do asyncpg (reproduzido manualmente
antes da correção). Aqui a task roda de verdade — sem `.delay()` — em threads separadas via
`asyncio.to_thread`, cada uma com seu próprio `asyncio.run()`, igual a duas execuções
sucessivas de um worker Celery real."""

import asyncio
import uuid

import pytest

from src.infrastructure.database.models.user import UserModel
from src.infrastructure.database.session import async_session_maker, engine
from src.infrastructure.queue import tasks as tasks_module
from src.infrastructure.queue.tasks import process_document_task
from src.infrastructure.repositories.document_repository import SqlAlchemyDocumentRepository
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.storage.local_storage import LocalFileStorage
from tests.fakes import FakeEmbeddingClient


async def test_task_is_a_no_op_for_unknown_document_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tasks_module, "get_embedding_client", lambda: FakeEmbeddingClient(dimensions=768)
    )
    await engine.dispose()

    await asyncio.to_thread(process_document_task, str(uuid.uuid4()))


class _FailingEmbeddingClient:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("provedor de embeddings indisponível")


async def _create_committed_document(filename: str, content: bytes) -> tuple[uuid.UUID, uuid.UUID]:
    """Cria usuário + documento com commit de verdade (fora do rollback usado nos outros
    testes), já que a task abre sua PRÓPRIA sessão via `async_session_maker()`, igual ao
    worker Celery real, e não enxergaria uma transação não commitada de outra conexão."""
    storage = LocalFileStorage()
    async with async_session_maker() as session:
        user = await SqlAlchemyUserRepository(session).create(
            email=f"task-{uuid.uuid4().hex[:10]}@example.com", hashed_password="hash"
        )
        storage_path = storage.save(user.id, filename, content)
        document = await SqlAlchemyDocumentRepository(session).create(
            owner_id=user.id,
            filename=filename,
            content_type="text/plain",
            size_bytes=len(content),
            storage_path=storage_path,
        )
    return user.id, document.id


async def _delete_user(user_id: uuid.UUID) -> None:
    async with async_session_maker() as session:
        db_user = await session.get(UserModel, user_id)
        if db_user is not None:
            await session.delete(db_user)
            await session.commit()


async def test_task_survives_two_consecutive_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cria os dois documentos e roda as duas tasks *de volta pra volta*, sem nenhum uso
    do engine pelo loop principal entre elas — assim a única conexão que a segunda task
    pode herdar do pool é a que a primeira deixou (ou não, se ela se limpou direito). É
    exatamente essa a situação que o `engine.dispose()` em tasks.py precisa cobrir; sem
    ele, a segunda chamada abaixo quebra com o `AttributeError`/`RuntimeError` original."""
    monkeypatch.setattr(
        tasks_module, "get_embedding_client", lambda: FakeEmbeddingClient(dimensions=768)
    )
    user_ids: list[uuid.UUID] = []
    document_ids: list[uuid.UUID] = []

    try:
        for i in range(2):
            user_id, document_id = await _create_committed_document(
                f"doc-{i}.txt", f"conteudo do documento numero {i}".encode()
            )
            user_ids.append(user_id)
            document_ids.append(document_id)

        await engine.dispose()  # limpa qualquer conexão que a preparação acima tenha deixado

        for document_id in document_ids:
            await asyncio.to_thread(process_document_task, str(document_id))

        for document_id in document_ids:
            async with async_session_maker() as session:
                refreshed = await SqlAlchemyDocumentRepository(session).get_by_id(document_id)
            assert refreshed is not None
            assert refreshed.status == "ready"
    finally:
        for user_id in user_ids:
            await _delete_user(user_id)


async def test_task_marks_document_as_failed_when_processing_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tasks_module, "get_embedding_client", lambda: _FailingEmbeddingClient())
    user_id, document_id = await _create_committed_document("doc.txt", b"conteudo qualquer")
    await engine.dispose()

    try:
        with pytest.raises(RuntimeError):
            await asyncio.to_thread(process_document_task, str(document_id))

        async with async_session_maker() as session:
            refreshed = await SqlAlchemyDocumentRepository(session).get_by_id(document_id)
        assert refreshed is not None
        assert refreshed.status == "failed"
    finally:
        await _delete_user(user_id)

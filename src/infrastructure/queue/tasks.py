import asyncio
from uuid import UUID

from src.application.services.document_processing_service import DocumentProcessingService
from src.infrastructure.ai.factory import get_embedding_client
from src.infrastructure.database.session import async_session_maker, engine
from src.infrastructure.queue.celery_app import celery_app
from src.infrastructure.repositories.document_chunk_repository import (
    SqlAlchemyDocumentChunkRepository,
)
from src.infrastructure.repositories.document_repository import SqlAlchemyDocumentRepository
from src.infrastructure.storage.local_storage import LocalFileStorage


async def _process_document(document_id: UUID) -> None:
    async with async_session_maker() as session:
        document_repository = SqlAlchemyDocumentRepository(session)
        document = await document_repository.get_by_id(document_id)
        if document is None:
            return

        try:
            await document_repository.update_status(document_id, "processing")

            content = LocalFileStorage().read(document.storage_path)
            chunk_repository = SqlAlchemyDocumentChunkRepository(session)
            processing_service = DocumentProcessingService(chunk_repository, get_embedding_client())
            await processing_service.process(document, content)

            await document_repository.update_status(document_id, "ready")
        except Exception:
            await document_repository.update_status(document_id, "failed")
            raise


@celery_app.task(name="process_document")  # type: ignore[untyped-decorator]
def process_document_task(document_id: str) -> None:
    """Roda num worker separado (processo próprio, sem acesso ao event loop do FastAPI),
    por isso cria seu próprio loop com asyncio.run() em vez de reusar código async direto.

    `engine` é um singleton de módulo, compartilhado com a API. Cada asyncio.run() cria e
    fecha um event loop novo, mas as conexões do pool do asyncpg ficam presas ao loop em
    que nasceram — sem o dispose(), a próxima task pega uma conexão presa a um loop já
    fechado e quebra com AttributeError dentro do asyncpg.
    """

    async def _run() -> None:
        try:
            await _process_document(UUID(document_id))
        finally:
            await engine.dispose()

    asyncio.run(_run())

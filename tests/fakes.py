"""Duplos de teste para os pontos de integração externa (IA e fila assíncrona).

Mantidos fora de conftest.py pra poderem ser importados também pelos testes unitários
dos services, sem puxar toda a infraestrutura de banco/app.
"""

import hashlib
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.document_processing_service import DocumentProcessingService
from src.domain.entities.chat_message import ChatMessage
from src.domain.repositories.embedding_client import EmbeddingClient
from src.domain.repositories.llm_client import LLMClient
from src.infrastructure.repositories.document_chunk_repository import (
    SqlAlchemyDocumentChunkRepository,
)
from src.infrastructure.repositories.document_repository import SqlAlchemyDocumentRepository
from src.infrastructure.storage.local_storage import LocalFileStorage


class FakeEmbeddingClient(EmbeddingClient):
    """Embeddings determinísticos derivados de um hash do texto — sem rede, sem Ollama,
    mas ainda assim distintos entre textos diferentes (útil pra testar ranking/busca)."""

    def __init__(self, dimensions: int) -> None:
        self._dimensions = dimensions
        self.calls: list[list[str]] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [self._vector_for(text) for text in texts]

    def _vector_for(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [digest[i % len(digest)] for i in range(self._dimensions)]
        norm = sum(v * v for v in raw) ** 0.5 or 1.0
        return [v / norm for v in raw]


class FakeLLMClient(LLMClient):
    """Não chama nenhum provedor de verdade — devolve uma resposta previsível que
    referencia a pergunta, suficiente pra testar o fluxo sem precisar do Ollama/OpenAI."""

    def __init__(self, reply: str | None = None) -> None:
        self._reply = reply
        self.calls: list[list[ChatMessage]] = []

    async def generate_reply(self, messages: list[ChatMessage]) -> str:
        self.calls.append(list(messages))
        if self._reply is not None:
            return self._reply
        last_user_message = next(m for m in reversed(messages) if m.role == "user")
        return f"[resposta fake] {last_user_message.content}"


class InlineTaskQueue:
    """Substitui o `CeleryTaskQueue` nos testes: em vez de publicar no Redis, só registra
    o id do documento; o teste dispara o processamento explicitamente com `run_pending()`,
    reusando a mesma sessão/transação do teste (assim o documento recém-criado, ainda não
    commitado de verdade, fica visível pro processamento sem precisar de uma conexão à parte
    — coisa que quebraria o isolamento por rollback usado nos outros testes)."""

    def __init__(self, session: AsyncSession, embedding_client: EmbeddingClient) -> None:
        self._session = session
        self._embedding_client = embedding_client
        self._pending: list[UUID] = []

    def enqueue_document_processing(self, document_id: UUID) -> None:
        self._pending.append(document_id)

    async def run_pending(self) -> None:
        while self._pending:
            document_id = self._pending.pop(0)
            await self._process(document_id)

    async def _process(self, document_id: UUID) -> None:
        document_repository = SqlAlchemyDocumentRepository(self._session)
        document = await document_repository.get_by_id(document_id)
        if document is None:
            return

        try:
            await document_repository.update_status(document_id, "processing")

            content = LocalFileStorage().read(document.storage_path)
            chunk_repository = SqlAlchemyDocumentChunkRepository(self._session)
            processing_service = DocumentProcessingService(
                chunk_repository, self._embedding_client
            )
            await processing_service.process(document, content)

            await document_repository.update_status(document_id, "ready")
        except Exception:
            await document_repository.update_status(document_id, "failed")
            raise

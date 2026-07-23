from uuid import UUID

from src.domain.entities.document import Document
from src.domain.repositories.document_chunk_repository import DocumentChunkRepository
from src.domain.repositories.embedding_client import EmbeddingClient
from src.infrastructure.config import get_settings
from src.infrastructure.text.chunker import chunk_text
from src.infrastructure.text.pdf_extractor import extract_text


class DocumentProcessingService:
    """Extrai texto, divide em chunks e gera embeddings.

    Hoje isso roda de forma síncrona dentro do próprio request de upload — na Fase 3
    (processamento assíncrono) essa mesma lógica passa a rodar dentro de uma task Celery,
    sem precisar mudar nada aqui, só quem chama.
    """

    def __init__(
        self, chunk_repository: DocumentChunkRepository, embedding_client: EmbeddingClient
    ) -> None:
        self._chunks = chunk_repository
        self._embeddings = embedding_client

    async def process(self, document: Document, content: bytes) -> None:
        settings = get_settings()

        text = extract_text(content, document.content_type)
        pieces = chunk_text(text, settings.chunk_size_chars, settings.chunk_overlap_chars)
        if not pieces:
            return

        embeddings = await self._embeddings.embed(pieces)
        await self._chunks.create_many(document.id, document.owner_id, pieces, embeddings)

    async def delete_chunks(self, document_id: UUID) -> None:
        await self._chunks.delete_by_document(document_id)

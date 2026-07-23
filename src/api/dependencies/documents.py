from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.db import get_db
from src.application.services.document_processing_service import DocumentProcessingService
from src.application.services.document_service import DocumentService
from src.domain.repositories.document_chunk_repository import DocumentChunkRepository
from src.domain.repositories.document_repository import DocumentRepository
from src.domain.repositories.embedding_client import EmbeddingClient
from src.infrastructure.ai.factory import get_embedding_client
from src.infrastructure.repositories.document_chunk_repository import (
    SqlAlchemyDocumentChunkRepository,
)
from src.infrastructure.repositories.document_repository import SqlAlchemyDocumentRepository
from src.infrastructure.storage.local_storage import LocalFileStorage


def get_document_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> DocumentRepository:
    return SqlAlchemyDocumentRepository(db)


def get_document_chunk_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentChunkRepository:
    return SqlAlchemyDocumentChunkRepository(db)


def get_document_processing_service(
    chunk_repository: Annotated[DocumentChunkRepository, Depends(get_document_chunk_repository)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
) -> DocumentProcessingService:
    return DocumentProcessingService(chunk_repository, embedding_client)


def get_document_service(
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    processing_service: Annotated[
        DocumentProcessingService, Depends(get_document_processing_service)
    ],
) -> DocumentService:
    return DocumentService(document_repository, LocalFileStorage(), processing_service)

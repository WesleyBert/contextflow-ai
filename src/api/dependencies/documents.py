from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.db import get_db
from src.application.services.document_service import DocumentService
from src.domain.repositories.document_repository import DocumentRepository
from src.infrastructure.repositories.document_repository import SqlAlchemyDocumentRepository
from src.infrastructure.storage.local_storage import LocalFileStorage


def get_document_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> DocumentRepository:
    return SqlAlchemyDocumentRepository(db)


def get_document_service(
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> DocumentService:
    return DocumentService(document_repository, LocalFileStorage())

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.db import get_db
from src.api.dependencies.documents import get_document_chunk_repository
from src.application.services.conversation_service import ConversationService
from src.application.services.rag_service import RAGService
from src.domain.repositories.conversation_repository import ConversationRepository
from src.domain.repositories.document_chunk_repository import DocumentChunkRepository
from src.domain.repositories.embedding_client import EmbeddingClient
from src.domain.repositories.llm_client import LLMClient
from src.infrastructure.ai.factory import get_embedding_client, get_llm_client
from src.infrastructure.repositories.conversation_repository import (
    SqlAlchemyConversationRepository,
)


def get_conversation_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationRepository:
    return SqlAlchemyConversationRepository(db)


def get_rag_service(
    chunk_repository: Annotated[DocumentChunkRepository, Depends(get_document_chunk_repository)],
    embedding_client: Annotated[EmbeddingClient, Depends(get_embedding_client)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> RAGService:
    return RAGService(chunk_repository, embedding_client, llm_client)


def get_conversation_service(
    conversation_repository: Annotated[
        ConversationRepository, Depends(get_conversation_repository)
    ],
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> ConversationService:
    return ConversationService(conversation_repository, rag_service)

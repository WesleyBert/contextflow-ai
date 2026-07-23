from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.db import get_db
from src.application.services.conversation_service import ConversationService
from src.domain.repositories.conversation_repository import ConversationRepository
from src.domain.repositories.llm_client import LLMClient
from src.infrastructure.ai.factory import get_llm_client
from src.infrastructure.repositories.conversation_repository import (
    SqlAlchemyConversationRepository,
)


def get_conversation_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationRepository:
    return SqlAlchemyConversationRepository(db)


def get_conversation_service(
    conversation_repository: Annotated[
        ConversationRepository, Depends(get_conversation_repository)
    ],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> ConversationService:
    return ConversationService(conversation_repository, llm_client)

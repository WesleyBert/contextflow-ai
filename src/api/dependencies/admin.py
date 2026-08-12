from typing import Annotated

from fastapi import Depends

from src.api.dependencies.conversations import get_ai_interaction_repository
from src.api.dependencies.documents import get_document_repository
from src.application.services.admin_metrics_service import AdminMetricsService
from src.domain.repositories.ai_interaction_repository import AiInteractionRepository
from src.domain.repositories.document_repository import DocumentRepository


def get_admin_metrics_service(
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    ai_interaction_repository: Annotated[
        AiInteractionRepository, Depends(get_ai_interaction_repository)
    ],
) -> AdminMetricsService:
    return AdminMetricsService(document_repository, ai_interaction_repository)

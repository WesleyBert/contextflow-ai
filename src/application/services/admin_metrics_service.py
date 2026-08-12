from dataclasses import dataclass

from src.domain.repositories.ai_interaction_repository import AiInteractionRepository, ModelUsage
from src.domain.repositories.document_repository import DocumentRepository


@dataclass
class AdminMetrics:
    documents_total: int
    documents_ready: int
    documents_failed: int
    document_error_rate: float
    avg_document_processing_time_ms: float | None
    total_questions: int
    chat_error_rate: float
    avg_chat_response_time_ms: float | None
    estimated_token_cost_usd: float
    most_used_models: list[ModelUsage]


class AdminMetricsService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        ai_interaction_repository: AiInteractionRepository,
    ) -> None:
        self._documents = document_repository
        self._ai_interactions = ai_interaction_repository

    async def get_metrics(self) -> AdminMetrics:
        processing_stats = await self._documents.processing_stats()
        chat_stats = await self._ai_interactions.chat_stats()

        document_error_rate = (
            processing_stats.failed / processing_stats.total if processing_stats.total else 0.0
        )
        chat_failed = chat_stats.total - chat_stats.succeeded
        chat_error_rate = chat_failed / chat_stats.total if chat_stats.total else 0.0

        return AdminMetrics(
            documents_total=processing_stats.total,
            documents_ready=processing_stats.ready,
            documents_failed=processing_stats.failed,
            document_error_rate=round(document_error_rate, 4),
            avg_document_processing_time_ms=processing_stats.avg_processing_time_ms,
            total_questions=chat_stats.total,
            chat_error_rate=round(chat_error_rate, 4),
            avg_chat_response_time_ms=chat_stats.avg_duration_ms,
            estimated_token_cost_usd=chat_stats.total_cost_estimate_usd,
            most_used_models=chat_stats.most_used_models,
        )

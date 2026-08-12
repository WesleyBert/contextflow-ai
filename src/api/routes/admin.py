from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies.admin import get_admin_metrics_service
from src.api.dependencies.auth import get_current_admin_user
from src.api.schemas.admin import AdminMetricsResponse, ModelUsageResponse
from src.application.services.admin_metrics_service import AdminMetricsService
from src.domain.entities.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics", response_model=AdminMetricsResponse)
async def get_admin_metrics(
    _current_user: Annotated[User, Depends(get_current_admin_user)],
    admin_metrics_service: Annotated[AdminMetricsService, Depends(get_admin_metrics_service)],
) -> AdminMetricsResponse:
    metrics = await admin_metrics_service.get_metrics()
    return AdminMetricsResponse(
        documents_total=metrics.documents_total,
        documents_ready=metrics.documents_ready,
        documents_failed=metrics.documents_failed,
        document_error_rate=metrics.document_error_rate,
        avg_document_processing_time_ms=metrics.avg_document_processing_time_ms,
        total_questions=metrics.total_questions,
        chat_error_rate=metrics.chat_error_rate,
        avg_chat_response_time_ms=metrics.avg_chat_response_time_ms,
        estimated_token_cost_usd=metrics.estimated_token_cost_usd,
        most_used_models=[
            ModelUsageResponse(provider=m.provider, model=m.model, count=m.count)
            for m in metrics.most_used_models
        ],
    )

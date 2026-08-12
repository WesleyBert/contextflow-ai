from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.application.services.admin_metrics_service import AdminMetricsService
from src.domain.repositories.ai_interaction_repository import ModelUsage
from tests.unit.repo_fakes import FakeAiInteractionRepository, FakeDocumentRepository


@pytest.fixture
def document_repository() -> FakeDocumentRepository:
    return FakeDocumentRepository()


@pytest.fixture
def ai_interaction_repository() -> FakeAiInteractionRepository:
    return FakeAiInteractionRepository()


@pytest.fixture
def admin_metrics_service(
    document_repository: FakeDocumentRepository,
    ai_interaction_repository: FakeAiInteractionRepository,
) -> AdminMetricsService:
    return AdminMetricsService(document_repository, ai_interaction_repository)


async def test_get_metrics_with_no_data(admin_metrics_service: AdminMetricsService) -> None:
    metrics = await admin_metrics_service.get_metrics()

    assert metrics.documents_total == 0
    assert metrics.document_error_rate == 0.0
    assert metrics.total_questions == 0
    assert metrics.chat_error_rate == 0.0
    assert metrics.avg_chat_response_time_ms is None
    assert metrics.most_used_models == []


async def test_get_metrics_computes_document_stats(
    admin_metrics_service: AdminMetricsService, document_repository: FakeDocumentRepository
) -> None:
    owner_id = uuid4()
    ready = await document_repository.create(owner_id, "a.txt", "text/plain", 10, "path/a")
    await document_repository.update_status(
        ready.id, "processing", started_at=datetime.now(UTC) - timedelta(seconds=2)
    )
    await document_repository.update_status(ready.id, "ready", finished_at=datetime.now(UTC))

    failed = await document_repository.create(owner_id, "b.txt", "text/plain", 10, "path/b")
    await document_repository.update_status(failed.id, "failed")

    metrics = await admin_metrics_service.get_metrics()

    assert metrics.documents_total == 2
    assert metrics.documents_ready == 1
    assert metrics.documents_failed == 1
    assert metrics.document_error_rate == 0.5
    assert metrics.avg_document_processing_time_ms is not None
    assert metrics.avg_document_processing_time_ms > 0


async def test_get_metrics_computes_chat_stats(
    admin_metrics_service: AdminMetricsService,
    ai_interaction_repository: FakeAiInteractionRepository,
) -> None:
    owner_id = uuid4()
    conversation_id = uuid4()
    await ai_interaction_repository.create(
        owner_id=owner_id,
        conversation_id=conversation_id,
        provider="ollama",
        model="llama3.2:3b",
        prompt_tokens_estimate=10,
        completion_tokens_estimate=20,
        cost_estimate_usd=0.0,
        duration_ms=100.0,
        succeeded=True,
    )
    await ai_interaction_repository.create(
        owner_id=owner_id,
        conversation_id=conversation_id,
        provider="ollama",
        model="llama3.2:3b",
        prompt_tokens_estimate=5,
        completion_tokens_estimate=0,
        cost_estimate_usd=0.0,
        duration_ms=50.0,
        succeeded=False,
    )

    metrics = await admin_metrics_service.get_metrics()

    assert metrics.total_questions == 2
    assert metrics.chat_error_rate == 0.5
    assert metrics.avg_chat_response_time_ms == 100.0
    assert metrics.most_used_models == [
        ModelUsage(provider="ollama", model="llama3.2:3b", count=2)
    ]

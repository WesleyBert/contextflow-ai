import logging

import pytest
from httpx import AsyncClient


async def test_response_includes_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


async def test_response_echoes_client_supplied_request_id(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/health", headers={"X-Request-ID": "meu-id-de-rastreio"}
    )

    assert response.headers["x-request-id"] == "meu-id-de-rastreio"


async def test_different_requests_get_different_request_ids(client: AsyncClient) -> None:
    first = await client.get("/api/v1/health")
    second = await client.get("/api/v1/health")

    assert first.headers["x-request-id"] != second.headers["x-request-id"]


async def test_request_completed_log_has_expected_fields(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="src.api.middlewares.request_logging"):
        response = await client.get("/api/v1/health")

    records = [r for r in caplog.records if r.message == "request completed"]
    assert len(records) == 1
    record = records[0]
    assert record.method == "GET"  # type: ignore[attr-defined]
    assert record.path == "/api/v1/health"  # type: ignore[attr-defined]
    assert record.status_code == 200  # type: ignore[attr-defined]
    assert record.request_id == response.headers["x-request-id"]  # type: ignore[attr-defined]
    assert record.duration_ms >= 0  # type: ignore[attr-defined]

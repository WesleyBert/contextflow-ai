from httpx import AsyncClient


async def test_metrics_endpoint_exposes_prometheus_format(client: AsyncClient) -> None:
    await client.get("/api/v1/health")

    response = await client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text

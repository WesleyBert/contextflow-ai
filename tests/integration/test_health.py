from httpx import AsyncClient


async def test_health_check_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_check_allows_configured_cors_origin(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/health", headers={"Origin": "http://localhost:5173"}
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

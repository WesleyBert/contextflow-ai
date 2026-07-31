"""Testes do rate limiting de verdade — usam o `RedisRateLimiter` real (Redis local,
o mesmo do docker-compose), diferente do `client` padrão em conftest.py, que sobrescreve
`get_rate_limiter` com um fake que nunca limita (senão qualquer teste com várias chamadas
de auth/upload esbarraria no limite, já que todas as requisições de teste compartilham o
mesmo IP falso do ASGITransport — confirmado: `request.client.host == "127.0.0.1"`)."""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.db import get_db
from src.api.dependencies.documents import get_task_queue
from src.api.dependencies.rate_limit import get_rate_limiter
from src.infrastructure.ai.factory import get_embedding_client, get_llm_client
from src.infrastructure.config import get_settings
from src.infrastructure.rate_limit.redis_rate_limiter import RedisRateLimiter, redis_client
from src.main import create_app
from tests.conftest import auth_headers, register_and_login
from tests.fakes import FakeEmbeddingClient, FakeLLMClient, InlineTaskQueue


@pytest_asyncio.fixture
async def rate_limited_client(
    db_session: AsyncSession,
    fake_embedding_client: FakeEmbeddingClient,
    fake_llm_client: FakeLLMClient,
    inline_task_queue: InlineTaskQueue,
) -> AsyncIterator[AsyncClient]:
    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_embedding_client] = lambda: fake_embedding_client
    app.dependency_overrides[get_llm_client] = lambda: fake_llm_client
    app.dependency_overrides[get_task_queue] = lambda: inline_task_queue
    app.dependency_overrides[get_rate_limiter] = lambda: RedisRateLimiter(redis_client)

    keys_to_clean = (
        "rate_limit:/api/v1/auth/register:127.0.0.1",
        "rate_limit:/api/v1/auth/login:127.0.0.1",
    )
    await redis_client.delete(*keys_to_clean)  # limpa resíduo de uma execução anterior

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
    finally:
        await redis_client.delete(*keys_to_clean)


async def test_register_blocks_after_limit_and_recovers_with_new_key(
    rate_limited_client: AsyncClient,
) -> None:
    limit = get_settings().rate_limit_auth_requests

    for i in range(limit):
        response = await rate_limited_client.post(
            "/api/v1/auth/register",
            json={"email": f"limite{i}@example.com", "password": "senha12345"},
        )
        assert response.status_code == 201, f"requisição {i} deveria ter passado"

    blocked = await rate_limited_client.post(
        "/api/v1/auth/register",
        json={"email": "vai-bloquear@example.com", "password": "senha12345"},
    )

    assert blocked.status_code == 429
    assert "error" in blocked.json()


async def test_login_and_register_have_independent_limits(
    rate_limited_client: AsyncClient,
) -> None:
    limit = get_settings().rate_limit_auth_requests

    for i in range(limit):
        response = await rate_limited_client.post(
            "/api/v1/auth/register",
            json={"email": f"separado{i}@example.com", "password": "senha12345"},
        )
        assert response.status_code == 201

    # Esgotou o limite de /register, mas /login usa uma chave própria (path na chave).
    login_response = await rate_limited_client.post(
        "/api/v1/auth/login",
        json={"email": "separado0@example.com", "password": "senha12345"},
    )

    assert login_response.status_code == 200


async def test_upload_blocks_after_limit_per_user(rate_limited_client: AsyncClient) -> None:
    token, user_id = await register_and_login(rate_limited_client)
    limit = get_settings().rate_limit_upload_requests

    try:
        for i in range(limit):
            response = await rate_limited_client.post(
                "/api/v1/documents",
                headers=auth_headers(token),
                files={"file": (f"doc-{i}.txt", b"conteudo", "text/plain")},
            )
            assert response.status_code == 201, f"upload {i} deveria ter passado"

        blocked = await rate_limited_client.post(
            "/api/v1/documents",
            headers=auth_headers(token),
            files={"file": ("vai-bloquear.txt", b"conteudo", "text/plain")},
        )

        assert blocked.status_code == 429
    finally:
        await redis_client.delete(f"rate_limit:upload:{user_id}")

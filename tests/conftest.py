"""Setup global de testes.

Aponta DATABASE_URL para um banco de teste dedicado (`contextflow_test`) *antes* de
qualquer módulo de `src` ser importado — o engine assíncrono em
`infrastructure/database/session.py` é um singleton criado na importação do módulo,
então isso precisa acontecer no topo deste arquivo, não dentro de uma fixture.
"""

import os
import uuid

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://contextflow:contextflow@localhost:5432/contextflow_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")
os.environ.setdefault("ADMIN_EMAILS", "admin@example.com")

from collections.abc import AsyncIterator  # noqa: E402

import asyncpg  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession  # noqa: E402

from src.api.dependencies.db import get_db  # noqa: E402
from src.api.dependencies.documents import get_task_queue  # noqa: E402
from src.api.dependencies.rate_limit import get_rate_limiter  # noqa: E402
from src.infrastructure.ai.factory import get_embedding_client, get_llm_client  # noqa: E402
from src.infrastructure.config import get_settings  # noqa: E402
from src.infrastructure.database.session import Base, engine  # noqa: E402
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository  # noqa: E402
from src.main import create_app  # noqa: E402
from tests.fakes import (  # noqa: E402
    FakeEmbeddingClient,
    FakeLLMClient,
    FakeRateLimiter,
    InlineTaskQueue,
)


async def _ensure_test_database_exists() -> None:
    settings = get_settings()
    assert "test" in settings.database_url, (
        "DATABASE_URL de teste precisa apontar pra um banco com 'test' no nome — "
        "isso evita rodar create_all/drop em cima do banco de desenvolvimento por engano."
    )

    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    target_db = dsn.rsplit("/", 1)[-1]
    admin_dsn = dsn.rsplit("/", 1)[0] + "/postgres"

    conn = await asyncpg.connect(admin_dsn)
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target_db)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{target_db}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_database() -> AsyncIterator[None]:
    await _ensure_test_database_exists()

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


@pytest_asyncio.fixture
async def db_connection() -> AsyncIterator[AsyncConnection]:
    async with engine.connect() as connection:
        yield connection


@pytest_asyncio.fixture
async def db_session(db_connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    """Sessão isolada por teste: roda numa transação externa que é sempre revertida no
    final, mesmo que o código testado chame `session.commit()` (vira um SAVEPOINT
    aninhado, graças ao join_transaction_mode padrão do SQLAlchemy 2.0)."""
    outer_transaction = await db_connection.begin()
    session = AsyncSession(bind=db_connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await outer_transaction.rollback()


@pytest_asyncio.fixture
async def fake_embedding_client() -> FakeEmbeddingClient:
    return FakeEmbeddingClient(dimensions=get_settings().embedding_dim)


@pytest_asyncio.fixture
async def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()


@pytest_asyncio.fixture
async def inline_task_queue(
    db_session: AsyncSession, fake_embedding_client: FakeEmbeddingClient
) -> InlineTaskQueue:
    """Substitui o Celery nos testes: quando `upload_document` enfileira, processa na hora,
    na mesma sessão/transação do teste, usando o embedding fake em vez de bater no Ollama."""
    return InlineTaskQueue(session=db_session, embedding_client=fake_embedding_client)


@pytest_asyncio.fixture
async def client(
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
    app.dependency_overrides[get_rate_limiter] = lambda: FakeRateLimiter()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def register_and_login(client: AsyncClient, email: str | None = None) -> tuple[str, str]:
    """Registra e loga um usuário via API, devolve (access_token, user_id)."""
    email = email or f"user-{uuid.uuid4().hex[:10]}@example.com"
    password = "senha12345"

    register_resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert register_resp.status_code == 201, register_resp.text
    user_id = register_resp.json()["id"]

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    return token, user_id


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_test_user(db_session: AsyncSession, email: str | None = None) -> uuid.UUID:
    """Cria um usuário direto no banco (sem passar pela API), pra satisfazer as foreign
    keys de owner_id nos testes de repositório que não precisam do fluxo de auth completo."""
    email = email or f"user-{uuid.uuid4().hex[:10]}@example.com"
    user = await SqlAlchemyUserRepository(db_session).create(email=email, hashed_password="hash")
    return user.id

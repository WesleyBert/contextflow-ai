from uuid import UUID, uuid4

from httpx import AsyncClient

from src.infrastructure.security.jwt import create_access_token, create_refresh_token
from tests.conftest import auth_headers, register_and_login


async def test_register_returns_created_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "nova@example.com", "password": "senha12345"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "nova@example.com"
    assert "hashed_password" not in body


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "duplicado@example.com", "password": "senha12345"}
    await client.post("/api/v1/auth/register", json=payload)

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"email": "x@example.com", "password": "curta"}
    )

    assert response.status_code == 422


async def test_login_returns_tokens(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "senha12345"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "senha12345"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login2@example.com", "password": "senha12345"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login2@example.com", "password": "senha-errada"},
    )

    assert response.status_code == 401


async def test_me_returns_current_user_with_valid_token(client: AsyncClient) -> None:
    token, user_id = await register_and_login(client)

    response = await client.get("/api/v1/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["id"] == user_id


async def test_me_rejects_missing_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code in (401, 403)


async def test_me_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer token-invalido"}
    )

    assert response.status_code == 401


async def test_me_rejects_refresh_token_used_as_access_token(client: AsyncClient) -> None:
    _, user_id = await register_and_login(client)
    refresh_token = create_refresh_token(UUID(user_id))

    response = await client.get("/api/v1/auth/me", headers=auth_headers(refresh_token))

    assert response.status_code == 401


async def test_me_rejects_token_for_deleted_or_unknown_user(client: AsyncClient) -> None:
    token_for_unknown_user = create_access_token(uuid4())

    response = await client.get("/api/v1/auth/me", headers=auth_headers(token_for_unknown_user))

    assert response.status_code == 401


async def test_refresh_returns_new_tokens(client: AsyncClient) -> None:
    _, user_id = await register_and_login(client)
    refresh_token = create_refresh_token(UUID(user_id))

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]

    me_response = await client.get("/api/v1/auth/me", headers=auth_headers(body["access_token"]))
    assert me_response.status_code == 200
    assert me_response.json()["id"] == user_id


async def test_refresh_rejects_access_token(client: AsyncClient) -> None:
    _, user_id = await register_and_login(client)
    access_token = create_access_token(UUID(user_id))

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access_token}
    )

    assert response.status_code == 401


async def test_refresh_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "token-invalido"}
    )

    assert response.status_code == 401


async def test_refresh_rejects_token_for_deleted_or_unknown_user(client: AsyncClient) -> None:
    refresh_token_for_unknown_user = create_refresh_token(uuid4())

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token_for_unknown_user}
    )

    assert response.status_code == 401

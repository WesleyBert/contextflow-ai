from httpx import AsyncClient

from tests.conftest import auth_headers, register_and_login
from tests.fakes import FakeLLMClient


async def test_upload_with_same_idempotency_key_returns_cached_document(
    client: AsyncClient,
) -> None:
    token, _ = await register_and_login(client)
    headers = {**auth_headers(token), "Idempotency-Key": "upload-abc"}

    first = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("doc.txt", b"conteudo", "text/plain")},
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("outro.txt", b"outro conteudo", "text/plain")},
    )
    assert second.status_code == 201, second.text
    assert second.json() == first.json()

    listed = await client.get("/api/v1/documents", headers=auth_headers(token))
    assert listed.json()["total"] == 1


async def test_upload_without_idempotency_key_is_not_deduplicated(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    for _ in range(2):
        response = await client.post(
            "/api/v1/documents",
            headers=auth_headers(token),
            files={"file": ("doc.txt", b"conteudo", "text/plain")},
        )
        assert response.status_code == 201

    listed = await client.get("/api/v1/documents", headers=auth_headers(token))
    assert listed.json()["total"] == 2


async def test_send_message_with_same_idempotency_key_calls_llm_once(
    client: AsyncClient, fake_llm_client: FakeLLMClient
) -> None:
    token, _ = await register_and_login(client)
    conversation = await client.post(
        "/api/v1/conversations", headers=auth_headers(token), json={"title": "Conversa"}
    )
    conversation_id = conversation.json()["id"]
    headers = {**auth_headers(token), "Idempotency-Key": "msg-abc"}

    first = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": "Qual a capital do Brasil?"},
    )
    assert first.status_code == 200, first.text

    second = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": "Qual a capital do Brasil?"},
    )
    assert second.status_code == 200, second.text
    assert second.json() == first.json()
    assert len(fake_llm_client.calls) == 1

    messages = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers=auth_headers(token)
    )
    assert len(messages.json()) == 2

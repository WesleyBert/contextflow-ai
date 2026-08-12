from httpx import AsyncClient

from tests.conftest import auth_headers, register_and_login
from tests.fakes import InlineTaskQueue


async def test_create_and_list_conversations(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    create_response = await client.post(
        "/api/v1/conversations", headers=auth_headers(token), json={"title": "Minha conversa"}
    )
    assert create_response.status_code == 201
    assert create_response.json()["title"] == "Minha conversa"

    list_response = await client.get("/api/v1/conversations", headers=auth_headers(token))
    assert list_response.status_code == 200
    body = list_response.json()
    assert [c["title"] for c in body["items"]] == ["Minha conversa"]
    assert body["total"] == 1


async def test_list_conversations_paginates_and_orders_by_title(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)
    for title in ("Charlie", "Alpha", "Bravo"):
        await client.post(
            "/api/v1/conversations", headers=auth_headers(token), json={"title": title}
        )

    response = await client.get(
        "/api/v1/conversations",
        headers=auth_headers(token),
        params={"page": 1, "page_size": 2, "order_by": "title_asc"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["pages"] == 2
    assert [c["title"] for c in body["items"]] == ["Alpha", "Bravo"]


async def test_list_conversations_filters_by_title_search(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)
    await client.post(
        "/api/v1/conversations",
        headers=auth_headers(token),
        json={"title": "Dúvidas sobre contrato"},
    )
    await client.post(
        "/api/v1/conversations", headers=auth_headers(token), json={"title": "Resumo de reunião"}
    )

    response = await client.get(
        "/api/v1/conversations", headers=auth_headers(token), params={"q": "contrato"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Dúvidas sobre contrato"


async def test_list_conversations_rejects_invalid_order_by(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.get(
        "/api/v1/conversations", headers=auth_headers(token), params={"order_by": "chutometro"}
    )

    assert response.status_code == 422


async def test_create_conversation_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/v1/conversations", json={"title": "Conversa"})

    assert response.status_code in (401, 403)


async def test_create_conversation_rejects_empty_title(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.post(
        "/api/v1/conversations", headers=auth_headers(token), json={"title": ""}
    )

    assert response.status_code == 422


async def test_send_message_returns_ai_reply(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)
    conversation = (
        await client.post(
            "/api/v1/conversations", headers=auth_headers(token), json={"title": "Conversa"}
        )
    ).json()

    response = await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_headers(token),
        json={"content": "qual a capital do brasil?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_message"]["content"] == "qual a capital do brasil?"
    assert body["user_message"]["role"] == "user"
    assert body["assistant_message"]["role"] == "assistant"
    assert "qual a capital do brasil?" in body["assistant_message"]["content"]


async def test_send_message_cites_sources_from_processed_document(
    client: AsyncClient, inline_task_queue: InlineTaskQueue
) -> None:
    token, _ = await register_and_login(client)
    await client.post(
        "/api/v1/documents",
        headers=auth_headers(token),
        files={"file": ("fatos.txt", b"O nome do gato da Ana e Whiskers.", "text/plain")},
    )
    await inline_task_queue.run_pending()

    conversation = (
        await client.post(
            "/api/v1/conversations", headers=auth_headers(token), json={"title": "Conversa"}
        )
    ).json()

    response = await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_headers(token),
        json={"content": "qual o nome do gato da ana?"},
    )

    assert response.status_code == 200
    sources = response.json()["assistant_message"]["sources"]
    assert len(sources) == 1
    assert sources[0]["document_filename"] == "fatos.txt"


async def test_messages_isolated_between_users_documents(
    client: AsyncClient, inline_task_queue: InlineTaskQueue
) -> None:
    token_a, _ = await register_and_login(client)
    await client.post(
        "/api/v1/documents",
        headers=auth_headers(token_a),
        files={"file": ("segredo.txt", b"O codigo secreto e 42.", "text/plain")},
    )
    await inline_task_queue.run_pending()

    token_b, _ = await register_and_login(client)
    conversation = (
        await client.post(
            "/api/v1/conversations", headers=auth_headers(token_b), json={"title": "Conversa"}
        )
    ).json()

    response = await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_headers(token_b),
        json={"content": "qual o codigo secreto?"},
    )

    assert response.status_code == 200
    assert response.json()["assistant_message"]["sources"] == []


async def test_list_messages_requires_ownership(client: AsyncClient) -> None:
    token_a, _ = await register_and_login(client)
    conversation = (
        await client.post(
            "/api/v1/conversations", headers=auth_headers(token_a), json={"title": "Conversa"}
        )
    ).json()
    token_b, _ = await register_and_login(client)

    response = await client.get(
        f"/api/v1/conversations/{conversation['id']}/messages", headers=auth_headers(token_b)
    )

    assert response.status_code == 403


async def test_list_messages_returns_404_for_unknown_conversation(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.get(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000000/messages",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


async def test_set_message_feedback_persists_and_is_reflected_in_messages(
    client: AsyncClient,
) -> None:
    token, _ = await register_and_login(client)
    conversation = (
        await client.post(
            "/api/v1/conversations", headers=auth_headers(token), json={"title": "Conversa"}
        )
    ).json()
    exchange = (
        await client.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            headers=auth_headers(token),
            json={"content": "qual a capital do brasil?"},
        )
    ).json()
    assistant_message_id = exchange["assistant_message"]["id"]

    response = await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages/{assistant_message_id}/feedback",
        headers=auth_headers(token),
        json={"rating": "up"},
    )

    assert response.status_code == 200
    assert response.json()["feedback"] == "up"

    messages = (
        await client.get(
            f"/api/v1/conversations/{conversation['id']}/messages", headers=auth_headers(token)
        )
    ).json()
    assistant_message = next(m for m in messages if m["id"] == assistant_message_id)
    assert assistant_message["feedback"] == "up"


async def test_set_message_feedback_rejects_user_message(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)
    conversation = (
        await client.post(
            "/api/v1/conversations", headers=auth_headers(token), json={"title": "Conversa"}
        )
    ).json()
    exchange = (
        await client.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            headers=auth_headers(token),
            json={"content": "qual a capital do brasil?"},
        )
    ).json()
    user_message_id = exchange["user_message"]["id"]

    response = await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages/{user_message_id}/feedback",
        headers=auth_headers(token),
        json={"rating": "up"},
    )

    assert response.status_code == 422

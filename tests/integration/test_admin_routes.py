from httpx import AsyncClient

from tests.conftest import auth_headers, register_and_login
from tests.fakes import InlineTaskQueue


async def test_admin_metrics_requires_admin_email(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.get("/api/v1/admin/metrics", headers=auth_headers(token))

    assert response.status_code == 403


async def test_admin_metrics_returns_data_for_admin_user(
    client: AsyncClient, inline_task_queue: InlineTaskQueue
) -> None:
    user_token, _ = await register_and_login(client)
    await client.post(
        "/api/v1/documents",
        headers=auth_headers(user_token),
        files={"file": ("doc.txt", b"conteudo", "text/plain")},
    )
    await inline_task_queue.run_pending()

    conversation = (
        await client.post(
            "/api/v1/conversations", headers=auth_headers(user_token), json={"title": "Conversa"}
        )
    ).json()
    await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_headers(user_token),
        json={"content": "qual a capital do brasil?"},
    )

    admin_token, _ = await register_and_login(client, email="admin@example.com")

    response = await client.get("/api/v1/admin/metrics", headers=auth_headers(admin_token))

    assert response.status_code == 200
    body = response.json()
    assert body["documents_total"] >= 1
    assert body["documents_ready"] >= 1
    assert body["total_questions"] >= 1
    assert isinstance(body["most_used_models"], list)

from httpx import AsyncClient

from tests.conftest import auth_headers, register_and_login
from tests.fakes import InlineTaskQueue


async def _upload_txt(
    client: AsyncClient,
    token: str,
    filename: str = "doc.txt",
    content: bytes = b"conteudo de teste",
) -> dict:
    response = await client.post(
        "/api/v1/documents",
        headers=auth_headers(token),
        files={"file": (filename, content, "text/plain")},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_upload_document_returns_pending_before_worker_runs(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    document = await _upload_txt(client, token)

    assert document["status"] == "pending"
    assert document["filename"] == "doc.txt"


async def test_upload_document_rejects_unsupported_content_type(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.post(
        "/api/v1/documents",
        headers=auth_headers(token),
        files={"file": ("malware.exe", b"conteudo", "application/x-msdownload")},
    )

    assert response.status_code == 422


async def test_upload_document_rejects_file_too_large(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.post(
        "/api/v1/documents",
        headers=auth_headers(token),
        files={"file": ("grande.txt", b"x" * (21 * 1024 * 1024), "text/plain")},
    )

    assert response.status_code == 422


async def test_upload_document_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/documents",
        files={"file": ("doc.txt", b"conteudo", "text/plain")},
    )

    assert response.status_code in (401, 403)


async def test_status_becomes_ready_after_worker_processes(
    client: AsyncClient, inline_task_queue: InlineTaskQueue
) -> None:
    token, _ = await register_and_login(client)
    document = await _upload_txt(client, token)

    await inline_task_queue.run_pending()

    response = await client.get(
        f"/api/v1/documents/{document['id']}/status", headers=auth_headers(token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_status_endpoint_requires_ownership(
    client: AsyncClient, inline_task_queue: InlineTaskQueue
) -> None:
    token_a, _ = await register_and_login(client)
    document = await _upload_txt(client, token_a)
    token_b, _ = await register_and_login(client)

    response = await client.get(
        f"/api/v1/documents/{document['id']}/status", headers=auth_headers(token_b)
    )

    assert response.status_code == 403


async def test_list_documents_returns_only_own_documents(client: AsyncClient) -> None:
    token_a, _ = await register_and_login(client)
    await _upload_txt(client, token_a, filename="meu.txt")
    token_b, _ = await register_and_login(client)
    await _upload_txt(client, token_b, filename="de-outro.txt")

    response = await client.get("/api/v1/documents", headers=auth_headers(token_a))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    filenames = [d["filename"] for d in body["items"]]
    assert filenames == ["meu.txt"]


async def test_list_documents_paginates(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)
    for i in range(3):
        await _upload_txt(client, token, filename=f"doc-{i}.txt")

    response = await client.get(
        "/api/v1/documents",
        headers=auth_headers(token),
        params={"page": 1, "page_size": 2, "order_by": "filename_asc"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["pages"] == 2
    assert [d["filename"] for d in body["items"]] == ["doc-0.txt", "doc-1.txt"]


async def test_list_documents_filters_by_status(
    client: AsyncClient, inline_task_queue: InlineTaskQueue
) -> None:
    token, _ = await register_and_login(client)
    await _upload_txt(client, token, filename="fica-pronto.txt")
    await inline_task_queue.run_pending()  # processa só o que já foi enfileirado até aqui
    await _upload_txt(client, token, filename="fica-pendente.txt")

    response = await client.get(
        "/api/v1/documents", headers=auth_headers(token), params={"status": "ready"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "fica-pronto.txt"


async def test_list_documents_filters_by_filename_search(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)
    await _upload_txt(client, token, filename="relatorio-financeiro.txt")
    await _upload_txt(client, token, filename="ata-reuniao.txt")

    response = await client.get(
        "/api/v1/documents", headers=auth_headers(token), params={"q": "financeiro"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "relatorio-financeiro.txt"


async def test_list_documents_rejects_invalid_order_by(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.get(
        "/api/v1/documents", headers=auth_headers(token), params={"order_by": "chutometro"}
    )

    assert response.status_code == 422


async def test_list_documents_rejects_page_size_above_limit(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.get(
        "/api/v1/documents", headers=auth_headers(token), params={"page_size": 101}
    )

    assert response.status_code == 422


async def test_list_documents_rejects_page_below_one(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)

    response = await client.get(
        "/api/v1/documents", headers=auth_headers(token), params={"page": 0}
    )

    assert response.status_code == 422


async def test_get_document_returns_document_for_owner(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)
    uploaded = await _upload_txt(client, token)

    response = await client.get(
        f"/api/v1/documents/{uploaded['id']}", headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["id"] == uploaded["id"]


async def test_status_stream_emits_events_until_ready(
    client: AsyncClient, inline_task_queue: InlineTaskQueue
) -> None:
    token, _ = await register_and_login(client)
    document = await _upload_txt(client, token)
    await inline_task_queue.run_pending()

    async with client.stream(
        "GET",
        f"/api/v1/documents/{document['id']}/status/stream",
        headers=auth_headers(token),
    ) as response:
        assert response.status_code == 200
        events = [line async for line in response.aiter_lines() if line.startswith("data:")]

    assert events
    assert '"status": "ready"' in events[-1]


async def test_get_document_returns_404_after_delete(client: AsyncClient) -> None:
    token, _ = await register_and_login(client)
    document = await _upload_txt(client, token)

    delete_response = await client.delete(
        f"/api/v1/documents/{document['id']}", headers=auth_headers(token)
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/documents/{document['id']}", headers=auth_headers(token)
    )
    assert get_response.status_code == 404


async def test_get_document_returns_403_for_other_owner(client: AsyncClient) -> None:
    token_a, _ = await register_and_login(client)
    document = await _upload_txt(client, token_a)
    token_b, _ = await register_and_login(client)

    response = await client.get(
        f"/api/v1/documents/{document['id']}", headers=auth_headers(token_b)
    )

    assert response.status_code == 403


async def test_delete_document_forbidden_for_other_owner(client: AsyncClient) -> None:
    token_a, _ = await register_and_login(client)
    document = await _upload_txt(client, token_a)
    token_b, _ = await register_and_login(client)

    response = await client.delete(
        f"/api/v1/documents/{document['id']}", headers=auth_headers(token_b)
    )

    assert response.status_code == 403

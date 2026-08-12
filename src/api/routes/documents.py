import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.documents import get_document_service
from src.api.dependencies.idempotency import get_idempotency_store
from src.api.dependencies.rate_limit import rate_limit_upload
from src.api.schemas.document import DocumentResponse, DocumentStatusResponse
from src.api.schemas.pagination import Page
from src.application.services.document_service import DocumentService
from src.domain.entities.document import DocumentStatus
from src.domain.entities.user import User
from src.domain.repositories.document_repository import DocumentOrderBy
from src.domain.repositories.idempotency_store import IdempotencyStore
from src.infrastructure.config import get_settings

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_upload)],
)
async def upload_document(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    idempotency_store: Annotated[IdempotencyStore, Depends(get_idempotency_store)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> DocumentResponse:
    cache_key = f"{current_user.id}:documents:{idempotency_key}" if idempotency_key else None
    if cache_key:
        cached = await idempotency_store.get(cache_key)
        if cached:
            return DocumentResponse.model_validate_json(cached)

    content = await file.read()
    document = await document_service.upload_document(
        owner_id=current_user.id,
        filename=file.filename or "arquivo",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    response = DocumentResponse(**document.__dict__)

    if cache_key:
        await idempotency_store.set(
            cache_key, response.model_dump_json(), get_settings().idempotency_ttl_seconds
        )
    return response


@router.get("", response_model=Page[DocumentResponse])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    document_status: Annotated[DocumentStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=255)] = None,
    order_by: Annotated[DocumentOrderBy, Query()] = "created_at_desc",
) -> Page[DocumentResponse]:
    documents, total = await document_service.list_documents(
        current_user.id,
        status=document_status,
        search=q,
        order_by=order_by,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return Page.of(
        items=[DocumentResponse(**d.__dict__) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    document = await document_service.get_document(current_user.id, document_id)
    return DocumentResponse(**document.__dict__)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> None:
    await document_service.delete_document(current_user.id, document_id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentStatusResponse:
    document = await document_service.get_document(current_user.id, document_id)
    return DocumentStatusResponse(id=document.id, status=document.status)


@router.get("/{document_id}/status/stream")
async def stream_document_status(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> StreamingResponse:
    # Valida existência/ownership antes de abrir o stream, pra erro 404/403
    # virar uma resposta HTTP normal em vez de quebrar no meio do SSE.
    await document_service.get_document(current_user.id, document_id)

    async def event_stream() -> AsyncIterator[str]:
        for _ in range(60):
            document = await document_service.get_document(current_user.id, document_id)
            payload = json.dumps({"id": str(document.id), "status": document.status})
            yield f"data: {payload}\n\n"
            if document.status in ("ready", "failed"):
                return
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

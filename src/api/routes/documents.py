from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.documents import get_document_service
from src.api.schemas.document import DocumentResponse
from src.application.services.document_service import DocumentService
from src.domain.entities.user import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    content = await file.read()
    document = await document_service.upload_document(
        owner_id=current_user.id,
        filename=file.filename or "arquivo",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    return DocumentResponse(**document.__dict__)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentResponse]:
    documents = await document_service.list_documents(current_user.id)
    return [DocumentResponse(**d.__dict__) for d in documents]


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

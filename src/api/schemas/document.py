from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    created_at: datetime


class DocumentStatusResponse(BaseModel):
    id: UUID
    status: DocumentStatus

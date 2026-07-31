from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

DocumentStatus = Literal["pending", "processing", "ready", "failed"]


@dataclass
class Document:
    id: UUID
    owner_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    status: DocumentStatus
    created_at: datetime

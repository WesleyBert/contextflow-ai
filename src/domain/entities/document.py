from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Document:
    id: UUID
    owner_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    created_at: datetime

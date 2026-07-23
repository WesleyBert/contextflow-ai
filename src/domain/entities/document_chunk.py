from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DocumentChunk:
    id: UUID
    document_id: UUID
    owner_id: UUID
    chunk_index: int
    content: str
    embedding: list[float]
    created_at: datetime


@dataclass
class RetrievedChunk:
    """Um chunk retornado por uma busca, junto com o quão relevante ele é."""

    chunk: DocumentChunk
    document_filename: str
    similarity: float

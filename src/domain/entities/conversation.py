from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

MessageRole = Literal["user", "assistant"]


@dataclass
class Conversation:
    id: UUID
    owner_id: UUID
    title: str
    created_at: datetime


@dataclass
class MessageSource:
    """Trecho de um documento usado pela IA pra montar a resposta — o que
    aparece pro usuário como 'fonte utilizada'."""

    document_id: UUID
    document_filename: str
    chunk_index: int
    snippet: str


@dataclass
class Message:
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    created_at: datetime
    sources: list[MessageSource] = field(default_factory=list)

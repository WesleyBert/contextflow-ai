from dataclasses import dataclass
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
class Message:
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    created_at: datetime

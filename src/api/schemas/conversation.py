from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)


class MessageSourceResponse(BaseModel):
    document_id: UUID
    document_filename: str
    chunk_index: int
    snippet: str


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources: list[MessageSourceResponse] = []
    feedback: Literal["up", "down"] | None = None
    created_at: datetime


class MessageExchangeResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class MessageFeedbackRequest(BaseModel):
    rating: Literal["up", "down"]

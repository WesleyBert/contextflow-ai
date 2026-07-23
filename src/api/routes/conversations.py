from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.conversations import get_conversation_service
from src.api.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessageExchangeResponse,
    MessageResponse,
)
from src.application.services.conversation_service import ConversationService
from src.domain.entities.user import User

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationResponse:
    conversation = await conversation_service.create_conversation(current_user.id, body.title)
    return ConversationResponse(**conversation.__dict__)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> list[ConversationResponse]:
    conversations = await conversation_service.list_conversations(current_user.id)
    return [ConversationResponse(**c.__dict__) for c in conversations]


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> list[MessageResponse]:
    messages = await conversation_service.get_messages(current_user.id, conversation_id)
    return [MessageResponse(**m.__dict__) for m in messages]


@router.post("/{conversation_id}/messages", response_model=MessageExchangeResponse)
async def send_message(
    conversation_id: UUID,
    body: MessageCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> MessageExchangeResponse:
    user_message, assistant_message = await conversation_service.send_message(
        current_user.id, conversation_id, body.content
    )
    return MessageExchangeResponse(
        user_message=MessageResponse(**user_message.__dict__),
        assistant_message=MessageResponse(**assistant_message.__dict__),
    )

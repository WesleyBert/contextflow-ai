from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.conversations import get_conversation_service
from src.api.dependencies.idempotency import get_idempotency_store
from src.api.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessageExchangeResponse,
    MessageFeedbackRequest,
    MessageResponse,
    MessageSourceResponse,
)
from src.api.schemas.pagination import Page
from src.application.services.conversation_service import ConversationService
from src.domain.entities.conversation import Message
from src.domain.entities.user import User
from src.domain.repositories.conversation_repository import ConversationOrderBy
from src.domain.repositories.idempotency_store import IdempotencyStore
from src.infrastructure.config import get_settings

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _to_message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        sources=[MessageSourceResponse(**source.__dict__) for source in message.sources],
        feedback=message.feedback,
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationResponse:
    conversation = await conversation_service.create_conversation(current_user.id, body.title)
    return ConversationResponse(**conversation.__dict__)


@router.get("", response_model=Page[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(max_length=255)] = None,
    order_by: Annotated[ConversationOrderBy, Query()] = "created_at_desc",
) -> Page[ConversationResponse]:
    conversations, total = await conversation_service.list_conversations(
        current_user.id,
        search=q,
        order_by=order_by,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return Page.of(
        items=[ConversationResponse(**c.__dict__) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> list[MessageResponse]:
    messages = await conversation_service.get_messages(current_user.id, conversation_id)
    return [_to_message_response(m) for m in messages]


@router.post("/{conversation_id}/messages", response_model=MessageExchangeResponse)
async def send_message(
    conversation_id: UUID,
    body: MessageCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
    idempotency_store: Annotated[IdempotencyStore, Depends(get_idempotency_store)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> MessageExchangeResponse:
    cache_key = (
        f"{current_user.id}:conversations:{conversation_id}:messages:{idempotency_key}"
        if idempotency_key
        else None
    )
    if cache_key:
        cached = await idempotency_store.get(cache_key)
        if cached:
            return MessageExchangeResponse.model_validate_json(cached)

    user_message, assistant_message = await conversation_service.send_message(
        current_user.id, conversation_id, body.content
    )
    response = MessageExchangeResponse(
        user_message=_to_message_response(user_message),
        assistant_message=_to_message_response(assistant_message),
    )

    if cache_key:
        await idempotency_store.set(
            cache_key, response.model_dump_json(), get_settings().idempotency_ttl_seconds
        )
    return response


@router.post("/{conversation_id}/messages/{message_id}/feedback", response_model=MessageResponse)
async def set_message_feedback(
    conversation_id: UUID,
    message_id: UUID,
    body: MessageFeedbackRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> MessageResponse:
    message = await conversation_service.set_message_feedback(
        current_user.id, conversation_id, message_id, body.rating
    )
    return _to_message_response(message)

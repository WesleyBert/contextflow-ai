from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.conversation import (
    Conversation,
    Message,
    MessageFeedback,
    MessageRole,
    MessageSource,
)
from src.domain.repositories.conversation_repository import ConversationOrderBy
from src.infrastructure.database.models.conversation import ConversationModel, MessageModel

_ORDER_COLUMNS: dict[ConversationOrderBy, ColumnElement[Any]] = {
    "created_at_desc": ConversationModel.created_at.desc(),
    "created_at_asc": ConversationModel.created_at.asc(),
    "title_asc": ConversationModel.title.asc(),
    "title_desc": ConversationModel.title.desc(),
}


def _conversation_to_entity(model: ConversationModel) -> Conversation:
    return Conversation(
        id=model.id,
        owner_id=model.owner_id,
        title=model.title,
        created_at=model.created_at,
    )


def _source_to_entity(source: dict[str, object]) -> MessageSource:
    return MessageSource(
        document_id=UUID(str(source["document_id"])),
        document_filename=str(source["document_filename"]),
        chunk_index=int(source["chunk_index"]),  # type: ignore[call-overload]
        snippet=str(source["snippet"]),
    )


def _message_to_entity(model: MessageModel) -> Message:
    return Message(
        id=model.id,
        conversation_id=model.conversation_id,
        role=model.role,  # type: ignore[arg-type]
        content=model.content,
        created_at=model.created_at,
        sources=[_source_to_entity(source) for source in model.sources],
        feedback=model.feedback,  # type: ignore[arg-type]
    )


class SqlAlchemyConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, owner_id: UUID, title: str) -> Conversation:
        model = ConversationModel(owner_id=owner_id, title=title)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _conversation_to_entity(model)

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        model = await self._session.get(ConversationModel, conversation_id)
        return _conversation_to_entity(model) if model else None

    async def list_by_owner(
        self,
        owner_id: UUID,
        *,
        search: str | None = None,
        order_by: ConversationOrderBy = "created_at_desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        filters = [ConversationModel.owner_id == owner_id]
        if search:
            filters.append(ConversationModel.title.ilike(f"%{search}%"))

        total = await self._session.scalar(
            select(func.count()).select_from(ConversationModel).where(*filters)
        )

        result = await self._session.execute(
            select(ConversationModel)
            .where(*filters)
            .order_by(_ORDER_COLUMNS[order_by])
            .limit(limit)
            .offset(offset)
        )
        conversations = [_conversation_to_entity(model) for model in result.scalars().all()]
        return conversations, total or 0

    async def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        sources: list[MessageSource] | None = None,
    ) -> Message:
        model = MessageModel(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=[
                {
                    "document_id": str(source.document_id),
                    "document_filename": source.document_filename,
                    "chunk_index": source.chunk_index,
                    "snippet": source.snippet,
                }
                for source in (sources or [])
            ],
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _message_to_entity(model)

    async def list_messages(self, conversation_id: UUID) -> list[Message]:
        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
        )
        return [_message_to_entity(model) for model in result.scalars().all()]

    async def get_message_by_id(self, message_id: UUID) -> Message | None:
        model = await self._session.get(MessageModel, message_id)
        return _message_to_entity(model) if model else None

    async def set_message_feedback(
        self, message_id: UUID, feedback: MessageFeedback
    ) -> Message | None:
        model = await self._session.get(MessageModel, message_id)
        if model is None:
            return None
        model.feedback = feedback
        await self._session.commit()
        await self._session.refresh(model)
        return _message_to_entity(model)

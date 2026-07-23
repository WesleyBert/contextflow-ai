from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.conversation import Conversation, Message, MessageRole
from src.infrastructure.database.models.conversation import ConversationModel, MessageModel


def _conversation_to_entity(model: ConversationModel) -> Conversation:
    return Conversation(
        id=model.id,
        owner_id=model.owner_id,
        title=model.title,
        created_at=model.created_at,
    )


def _message_to_entity(model: MessageModel) -> Message:
    return Message(
        id=model.id,
        conversation_id=model.conversation_id,
        role=model.role,  # type: ignore[arg-type]
        content=model.content,
        created_at=model.created_at,
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

    async def list_by_owner(self, owner_id: UUID) -> list[Conversation]:
        result = await self._session.execute(
            select(ConversationModel)
            .where(ConversationModel.owner_id == owner_id)
            .order_by(ConversationModel.created_at.desc())
        )
        return [_conversation_to_entity(model) for model in result.scalars().all()]

    async def add_message(self, conversation_id: UUID, role: MessageRole, content: str) -> Message:
        model = MessageModel(conversation_id=conversation_id, role=role, content=content)
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

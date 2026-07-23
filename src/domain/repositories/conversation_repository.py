from typing import Protocol
from uuid import UUID

from src.domain.entities.conversation import Conversation, Message, MessageRole


class ConversationRepository(Protocol):
    async def create(self, owner_id: UUID, title: str) -> Conversation: ...

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None: ...

    async def list_by_owner(self, owner_id: UUID) -> list[Conversation]: ...

    async def add_message(
        self, conversation_id: UUID, role: MessageRole, content: str
    ) -> Message: ...

    async def list_messages(self, conversation_id: UUID) -> list[Message]: ...

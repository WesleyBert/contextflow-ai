from typing import Literal, Protocol
from uuid import UUID

from src.domain.entities.conversation import Conversation, Message, MessageRole, MessageSource

ConversationOrderBy = Literal["created_at_desc", "created_at_asc", "title_asc", "title_desc"]


class ConversationRepository(Protocol):
    async def create(self, owner_id: UUID, title: str) -> Conversation: ...

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None: ...

    async def list_by_owner(
        self,
        owner_id: UUID,
        *,
        search: str | None = None,
        order_by: ConversationOrderBy = "created_at_desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        """Devolve (conversas da página, total de conversas que casam com o filtro)."""
        ...

    async def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        sources: list[MessageSource] | None = None,
    ) -> Message: ...

    async def list_messages(self, conversation_id: UUID) -> list[Message]: ...

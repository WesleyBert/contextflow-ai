from uuid import UUID

from src.domain.entities.conversation import Conversation, Message
from src.domain.exceptions.base import ForbiddenError, NotFoundError
from src.domain.repositories.conversation_repository import ConversationRepository
from src.domain.repositories.llm_client import LLMClient


class ConversationService:
    def __init__(
        self, conversation_repository: ConversationRepository, llm_client: LLMClient
    ) -> None:
        self._conversations = conversation_repository
        self._llm = llm_client

    async def create_conversation(self, owner_id: UUID, title: str) -> Conversation:
        return await self._conversations.create(owner_id=owner_id, title=title)

    async def list_conversations(self, owner_id: UUID) -> list[Conversation]:
        return await self._conversations.list_by_owner(owner_id)

    async def _get_owned_conversation(self, owner_id: UUID, conversation_id: UUID) -> Conversation:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversa não encontrada")
        if conversation.owner_id != owner_id:
            raise ForbiddenError("Você não tem acesso a esta conversa")
        return conversation

    async def get_messages(self, owner_id: UUID, conversation_id: UUID) -> list[Message]:
        await self._get_owned_conversation(owner_id, conversation_id)
        return await self._conversations.list_messages(conversation_id)

    async def send_message(
        self, owner_id: UUID, conversation_id: UUID, content: str
    ) -> tuple[Message, Message]:
        await self._get_owned_conversation(owner_id, conversation_id)

        user_message = await self._conversations.add_message(conversation_id, "user", content)

        history = await self._conversations.list_messages(conversation_id)
        reply_content = await self._llm.generate_reply(history)

        assistant_message = await self._conversations.add_message(
            conversation_id, "assistant", reply_content
        )

        return user_message, assistant_message

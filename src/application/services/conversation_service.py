import time
from uuid import UUID

from src.application.services.rag_service import RAGService
from src.domain.entities.conversation import Conversation, Message, MessageFeedback
from src.domain.exceptions.base import ForbiddenError, NotFoundError, ValidationError
from src.domain.repositories.ai_interaction_repository import AiInteractionRepository
from src.domain.repositories.conversation_repository import (
    ConversationOrderBy,
    ConversationRepository,
)
from src.infrastructure.config import Settings, get_settings
from src.infrastructure.text.token_estimator import estimate_tokens


class ConversationService:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        rag_service: RAGService,
        ai_interaction_repository: AiInteractionRepository,
    ) -> None:
        self._conversations = conversation_repository
        self._rag = rag_service
        self._ai_interactions = ai_interaction_repository

    async def create_conversation(self, owner_id: UUID, title: str) -> Conversation:
        return await self._conversations.create(owner_id=owner_id, title=title)

    async def list_conversations(
        self,
        owner_id: UUID,
        *,
        search: str | None = None,
        order_by: ConversationOrderBy = "created_at_desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        return await self._conversations.list_by_owner(
            owner_id, search=search, order_by=order_by, limit=limit, offset=offset
        )

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

        history_before = await self._conversations.list_messages(conversation_id)
        history_before = history_before[:-1]  # exclui a mensagem recém-criada acima

        settings = get_settings()
        provider = settings.ai_provider
        model = settings.ollama_model if provider == "ollama" else settings.openai_model
        prompt_tokens = estimate_tokens(content)
        start = time.perf_counter()

        try:
            reply_content, sources = await self._rag.answer(owner_id, history_before, content)
        except Exception:
            await self._ai_interactions.create(
                owner_id=owner_id,
                conversation_id=conversation_id,
                provider=provider,
                model=model,
                prompt_tokens_estimate=prompt_tokens,
                completion_tokens_estimate=0,
                cost_estimate_usd=self._estimate_cost(settings, prompt_tokens, 0),
                duration_ms=(time.perf_counter() - start) * 1000,
                succeeded=False,
            )
            raise

        completion_tokens = estimate_tokens(reply_content)
        await self._ai_interactions.create(
            owner_id=owner_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            prompt_tokens_estimate=prompt_tokens,
            completion_tokens_estimate=completion_tokens,
            cost_estimate_usd=self._estimate_cost(settings, prompt_tokens, completion_tokens),
            duration_ms=(time.perf_counter() - start) * 1000,
            succeeded=True,
        )

        assistant_message = await self._conversations.add_message(
            conversation_id, "assistant", reply_content, sources=sources
        )

        return user_message, assistant_message

    @staticmethod
    def _estimate_cost(settings: Settings, prompt_tokens: int, completion_tokens: int) -> float:
        prompt_cost = (prompt_tokens / 1000) * settings.token_price_per_1k_prompt_usd
        completion_cost = (completion_tokens / 1000) * settings.token_price_per_1k_completion_usd
        return prompt_cost + completion_cost

    async def set_message_feedback(
        self,
        owner_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        feedback: MessageFeedback,
    ) -> Message:
        await self._get_owned_conversation(owner_id, conversation_id)

        message = await self._conversations.get_message_by_id(message_id)
        if message is None or message.conversation_id != conversation_id:
            raise NotFoundError("Mensagem não encontrada")
        if message.role != "assistant":
            raise ValidationError("Só é possível avaliar respostas da IA")

        updated = await self._conversations.set_message_feedback(message_id, feedback)
        assert updated is not None  # já confirmamos que a mensagem existe acima
        return updated

from unittest.mock import create_autospec
from uuid import uuid4

import pytest

from src.application.services.conversation_service import ConversationService
from src.application.services.rag_service import RAGService
from src.domain.entities.conversation import MessageSource
from src.domain.exceptions.base import ForbiddenError, NotFoundError, ValidationError
from tests.unit.repo_fakes import FakeAiInteractionRepository, FakeConversationRepository


@pytest.fixture
def rag_service() -> RAGService:
    mock = create_autospec(RAGService, instance=True)
    mock.answer.return_value = ("resposta da ia", [])
    return mock


@pytest.fixture
def conversation_repository() -> FakeConversationRepository:
    return FakeConversationRepository()


@pytest.fixture
def ai_interaction_repository() -> FakeAiInteractionRepository:
    return FakeAiInteractionRepository()


@pytest.fixture
def conversation_service(
    conversation_repository: FakeConversationRepository,
    rag_service: RAGService,
    ai_interaction_repository: FakeAiInteractionRepository,
) -> ConversationService:
    return ConversationService(conversation_repository, rag_service, ai_interaction_repository)


async def test_create_and_list_conversations(conversation_service: ConversationService) -> None:
    owner_id = uuid4()
    await conversation_service.create_conversation(owner_id, "Minha conversa")

    conversations, total = await conversation_service.list_conversations(owner_id)

    assert [c.title for c in conversations] == ["Minha conversa"]
    assert total == 1


async def test_get_messages_raises_not_found_for_unknown_conversation(
    conversation_service: ConversationService,
) -> None:
    with pytest.raises(NotFoundError):
        await conversation_service.get_messages(uuid4(), uuid4())


async def test_get_messages_raises_forbidden_for_other_owner(
    conversation_service: ConversationService,
) -> None:
    conversation = await conversation_service.create_conversation(uuid4(), "Conversa")

    with pytest.raises(ForbiddenError):
        await conversation_service.get_messages(uuid4(), conversation.id)


async def test_send_message_persists_user_and_assistant_messages(
    conversation_service: ConversationService, rag_service: RAGService
) -> None:
    owner_id = uuid4()
    conversation = await conversation_service.create_conversation(owner_id, "Conversa")
    sources = [
        MessageSource(
            document_id=uuid4(), document_filename="doc.txt", chunk_index=0, snippet="trecho"
        )
    ]
    rag_service.answer.return_value = ("resposta baseada nos documentos", sources)  # type: ignore[attr-defined]

    user_message, assistant_message = await conversation_service.send_message(
        owner_id, conversation.id, "qual a capital do brasil?"
    )

    assert user_message.role == "user"
    assert user_message.content == "qual a capital do brasil?"
    assert assistant_message.role == "assistant"
    assert assistant_message.content == "resposta baseada nos documentos"
    assert assistant_message.sources == sources

    all_messages = await conversation_service.get_messages(owner_id, conversation.id)
    assert [m.role for m in all_messages] == ["user", "assistant"]


async def test_send_message_calls_rag_with_history_excluding_new_message(
    conversation_service: ConversationService,
    conversation_repository: FakeConversationRepository,
    rag_service: RAGService,
) -> None:
    owner_id = uuid4()
    conversation = await conversation_service.create_conversation(owner_id, "Conversa")
    await conversation_repository.add_message(conversation.id, "user", "pergunta antiga")
    await conversation_repository.add_message(conversation.id, "assistant", "resposta antiga")

    await conversation_service.send_message(owner_id, conversation.id, "pergunta nova")

    call_args = rag_service.answer.call_args  # type: ignore[attr-defined]
    _, history_arg, question_arg = call_args.args
    assert question_arg == "pergunta nova"
    assert [m.content for m in history_arg] == ["pergunta antiga", "resposta antiga"]


async def test_send_message_records_successful_ai_interaction(
    conversation_service: ConversationService,
    ai_interaction_repository: FakeAiInteractionRepository,
) -> None:
    owner_id = uuid4()
    conversation = await conversation_service.create_conversation(owner_id, "Conversa")

    await conversation_service.send_message(owner_id, conversation.id, "pergunta")

    assert len(ai_interaction_repository.interactions) == 1
    interaction = ai_interaction_repository.interactions[0]
    assert interaction.succeeded is True
    assert interaction.conversation_id == conversation.id
    assert interaction.owner_id == owner_id


async def test_send_message_records_failed_ai_interaction_and_reraises(
    conversation_service: ConversationService,
    ai_interaction_repository: FakeAiInteractionRepository,
    rag_service: RAGService,
) -> None:
    owner_id = uuid4()
    conversation = await conversation_service.create_conversation(owner_id, "Conversa")
    rag_service.answer.side_effect = RuntimeError("falha no LLM")  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError):
        await conversation_service.send_message(owner_id, conversation.id, "pergunta")

    assert len(ai_interaction_repository.interactions) == 1
    assert ai_interaction_repository.interactions[0].succeeded is False


async def test_send_message_raises_forbidden_for_other_owner(
    conversation_service: ConversationService,
) -> None:
    conversation = await conversation_service.create_conversation(uuid4(), "Conversa")

    with pytest.raises(ForbiddenError):
        await conversation_service.send_message(uuid4(), conversation.id, "oi")


async def test_set_message_feedback_on_assistant_message(
    conversation_service: ConversationService,
) -> None:
    owner_id = uuid4()
    conversation = await conversation_service.create_conversation(owner_id, "Conversa")
    _, assistant_message = await conversation_service.send_message(
        owner_id, conversation.id, "pergunta"
    )

    updated = await conversation_service.set_message_feedback(
        owner_id, conversation.id, assistant_message.id, "up"
    )

    assert updated.feedback == "up"


async def test_set_message_feedback_rejects_user_message(
    conversation_service: ConversationService,
) -> None:
    owner_id = uuid4()
    conversation = await conversation_service.create_conversation(owner_id, "Conversa")
    user_message, _ = await conversation_service.send_message(
        owner_id, conversation.id, "pergunta"
    )

    with pytest.raises(ValidationError):
        await conversation_service.set_message_feedback(
            owner_id, conversation.id, user_message.id, "down"
        )


async def test_set_message_feedback_raises_not_found_for_unknown_message(
    conversation_service: ConversationService,
) -> None:
    owner_id = uuid4()
    conversation = await conversation_service.create_conversation(owner_id, "Conversa")

    with pytest.raises(NotFoundError):
        await conversation_service.set_message_feedback(owner_id, conversation.id, uuid4(), "up")


async def test_set_message_feedback_raises_forbidden_for_other_owner(
    conversation_service: ConversationService,
) -> None:
    owner_id = uuid4()
    conversation = await conversation_service.create_conversation(owner_id, "Conversa")
    _, assistant_message = await conversation_service.send_message(
        owner_id, conversation.id, "pergunta"
    )

    with pytest.raises(ForbiddenError):
        await conversation_service.set_message_feedback(
            uuid4(), conversation.id, assistant_message.id, "up"
        )

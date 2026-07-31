from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.conversation import MessageSource
from src.infrastructure.repositories.conversation_repository import (
    SqlAlchemyConversationRepository,
)
from tests.conftest import create_test_user


async def test_create_and_get_conversation(db_session: AsyncSession) -> None:
    repository = SqlAlchemyConversationRepository(db_session)
    owner_id = await create_test_user(db_session)

    conversation = await repository.create(owner_id, "Minha conversa")

    fetched = await repository.get_by_id(conversation.id)
    assert fetched is not None
    assert fetched.title == "Minha conversa"
    assert fetched.owner_id == owner_id


async def test_list_by_owner_returns_only_owner_conversations(db_session: AsyncSession) -> None:
    repository = SqlAlchemyConversationRepository(db_session)
    owner_id = await create_test_user(db_session)
    other_owner_id = await create_test_user(db_session)
    await repository.create(owner_id, "Minha")
    await repository.create(other_owner_id, "De outro")

    conversations, total = await repository.list_by_owner(owner_id)

    assert [c.title for c in conversations] == ["Minha"]
    assert total == 1


async def test_list_by_owner_paginates_and_orders_by_title(db_session: AsyncSession) -> None:
    repository = SqlAlchemyConversationRepository(db_session)
    owner_id = await create_test_user(db_session)
    for title in ("Charlie", "Alpha", "Bravo"):
        await repository.create(owner_id, title)

    first_page, total = await repository.list_by_owner(
        owner_id, order_by="title_asc", limit=2, offset=0
    )
    second_page, _ = await repository.list_by_owner(
        owner_id, order_by="title_asc", limit=2, offset=2
    )

    assert total == 3
    assert [c.title for c in first_page] == ["Alpha", "Bravo"]
    assert [c.title for c in second_page] == ["Charlie"]


async def test_list_by_owner_filters_by_title_search(db_session: AsyncSession) -> None:
    repository = SqlAlchemyConversationRepository(db_session)
    owner_id = await create_test_user(db_session)
    await repository.create(owner_id, "Dúvidas sobre contrato")
    await repository.create(owner_id, "Resumo de reunião")

    conversations, total = await repository.list_by_owner(owner_id, search="contrato")

    assert total == 1
    assert conversations[0].title == "Dúvidas sobre contrato"


async def test_add_message_and_list_messages_in_order(db_session: AsyncSession) -> None:
    repository = SqlAlchemyConversationRepository(db_session)
    owner_id = await create_test_user(db_session)
    conversation = await repository.create(owner_id, "Conversa")

    await repository.add_message(conversation.id, "user", "primeira pergunta")
    await repository.add_message(conversation.id, "assistant", "primeira resposta")

    messages = await repository.list_messages(conversation.id)
    assert [(m.role, m.content) for m in messages] == [
        ("user", "primeira pergunta"),
        ("assistant", "primeira resposta"),
    ]


async def test_add_message_persists_sources(db_session: AsyncSession) -> None:
    repository = SqlAlchemyConversationRepository(db_session)
    owner_id = await create_test_user(db_session)
    conversation = await repository.create(owner_id, "Conversa")
    sources = [
        MessageSource(
            document_id=uuid4(), document_filename="doc.txt", chunk_index=2, snippet="trecho"
        )
    ]

    message = await repository.add_message(
        conversation.id, "assistant", "resposta com fonte", sources=sources
    )

    [persisted] = await repository.list_messages(conversation.id)
    assert persisted.id == message.id
    assert persisted.sources[0].document_filename == "doc.txt"
    assert persisted.sources[0].chunk_index == 2

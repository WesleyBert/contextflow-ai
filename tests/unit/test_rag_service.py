from datetime import UTC, datetime
from uuid import uuid4

from src.application.services.rag_service import RAGService
from src.domain.entities.conversation import Message
from src.domain.entities.document_chunk import DocumentChunk, RetrievedChunk
from tests.fakes import FakeEmbeddingClient, FakeLLMClient
from tests.unit.repo_fakes import FakeDocumentChunkRepository


def _make_retrieved_chunk(
    content: str, similarity: float, filename: str = "doc.txt"
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=DocumentChunk(
            id=uuid4(),
            document_id=uuid4(),
            owner_id=uuid4(),
            chunk_index=0,
            content=content,
            embedding=[0.1],
            created_at=datetime.now(UTC),
        ),
        document_filename=filename,
        similarity=similarity,
    )


async def test_answer_returns_sources_from_retrieved_chunks() -> None:
    chunk_repository = FakeDocumentChunkRepository()
    chunk_repository.search_results = [_make_retrieved_chunk("brasília é a capital", 0.9)]
    service = RAGService(chunk_repository, FakeEmbeddingClient(dimensions=8), FakeLLMClient())

    _, sources = await service.answer(uuid4(), [], "qual a capital do brasil?")

    assert len(sources) == 1
    assert sources[0].document_filename == "doc.txt"
    assert sources[0].snippet == "brasília é a capital"


async def test_answer_prompt_includes_context_when_chunks_found() -> None:
    chunk_repository = FakeDocumentChunkRepository()
    chunk_repository.search_results = [_make_retrieved_chunk("brasília é a capital do brasil", 0.9)]
    llm_client = FakeLLMClient()
    service = RAGService(chunk_repository, FakeEmbeddingClient(dimensions=8), llm_client)

    await service.answer(uuid4(), [], "qual a capital do brasil?")

    system_message = llm_client.calls[0][0]
    assert system_message.role == "system"
    assert "brasília é a capital do brasil" in system_message.content


async def test_answer_falls_back_to_general_knowledge_prompt_without_chunks() -> None:
    chunk_repository = FakeDocumentChunkRepository()
    llm_client = FakeLLMClient()
    service = RAGService(chunk_repository, FakeEmbeddingClient(dimensions=8), llm_client)

    _, sources = await service.answer(uuid4(), [], "qualquer pergunta")

    assert sources == []
    system_message = llm_client.calls[0][0]
    assert "não tem documentos processados" in system_message.content


async def test_answer_includes_conversation_history_between_system_and_question() -> None:
    chunk_repository = FakeDocumentChunkRepository()
    llm_client = FakeLLMClient()
    service = RAGService(chunk_repository, FakeEmbeddingClient(dimensions=8), llm_client)
    history = [
        Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role="user",
            content="mensagem anterior",
            created_at=datetime.now(UTC),
        )
    ]

    await service.answer(uuid4(), history, "pergunta atual")

    roles = [m.role for m in llm_client.calls[0]]
    assert roles == ["system", "user", "user"]
    assert llm_client.calls[0][1].content == "mensagem anterior"
    assert llm_client.calls[0][2].content == "pergunta atual"

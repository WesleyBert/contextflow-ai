from datetime import UTC, datetime
from uuid import uuid4

from src.domain.entities.document_chunk import DocumentChunk, RetrievedChunk
from src.infrastructure.text.reranker import rerank


def _make_candidate(content: str, similarity: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=DocumentChunk(
            id=uuid4(),
            document_id=uuid4(),
            owner_id=uuid4(),
            chunk_index=0,
            content=content,
            embedding=[0.0],
            created_at=datetime.now(UTC),
        ),
        document_filename="doc.txt",
        similarity=similarity,
    )


def test_empty_candidates_returns_empty() -> None:
    assert rerank("qualquer pergunta", [], top_k=5) == []


def test_query_without_meaningful_tokens_falls_back_to_similarity_order() -> None:
    candidates = [_make_candidate("a", 0.5), _make_candidate("b", 0.9)]

    result = rerank("é a o", candidates, top_k=5)

    assert result == candidates[:5]


def test_respects_top_k_limit() -> None:
    candidates = [_make_candidate(f"conteudo sobre gatos {i}", 0.5) for i in range(10)]

    result = rerank("gatos", candidates, top_k=3)

    assert len(result) == 3


def test_lexical_overlap_can_beat_higher_similarity() -> None:
    high_similarity_no_overlap = _make_candidate("informação totalmente não relacionada", 0.95)
    lower_similarity_exact_match = _make_candidate(
        "a capital da frança é paris, cidade luz", 0.6
    )

    candidates = [high_similarity_no_overlap, lower_similarity_exact_match]
    result = rerank("qual a capital da frança", candidates, top_k=1)

    assert result == [lower_similarity_exact_match]

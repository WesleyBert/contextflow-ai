import re

from src.domain.entities.document_chunk import RetrievedChunk

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text) if len(w) > 2}


def rerank(query: str, candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """Segundo estágio de retrieval: a busca vetorial (`search_similar`) já trouxe os
    candidatos mais próximos semanticamente; aqui reordenamos misturando essa similaridade
    com sobreposição léxica (quantas palavras da pergunta aparecem literalmente no chunk).
    Isso ajuda em casos onde um chunk semanticamente "parecido" não tem o termo exato que o
    usuário perguntou, e um outro, mais textualmente próximo, tem — sem precisar de um
    modelo de cross-encoder dedicado."""
    query_tokens = _tokenize(query)
    if not query_tokens or not candidates:
        return candidates[:top_k]

    def score(candidate: RetrievedChunk) -> float:
        chunk_tokens = _tokenize(candidate.chunk.content)
        overlap = len(query_tokens & chunk_tokens) / len(query_tokens)
        return 0.6 * candidate.similarity + 0.4 * overlap

    return sorted(candidates, key=score, reverse=True)[:top_k]

from uuid import UUID

from src.domain.entities.chat_message import ChatMessage
from src.domain.entities.conversation import Message, MessageSource
from src.domain.entities.document_chunk import RetrievedChunk
from src.domain.repositories.document_chunk_repository import DocumentChunkRepository
from src.domain.repositories.embedding_client import EmbeddingClient
from src.domain.repositories.llm_client import LLMClient
from src.infrastructure.config import get_settings
from src.infrastructure.text.reranker import rerank

_SNIPPET_LENGTH = 280

_SYSTEM_PROMPT_WITH_CONTEXT = (
    "Você é um assistente que responde perguntas com base no contexto abaixo, extraído "
    "dos documentos do usuário. Use apenas essas informações para responder. Se a resposta "
    "não estiver no contexto, diga claramente que não encontrou isso nos documentos.\n\n"
    "Contexto:\n{context}"
)

_SYSTEM_PROMPT_NO_CONTEXT = (
    "Você é um assistente útil. O usuário ainda não tem documentos processados que sejam "
    "relevantes pra essa pergunta, então responda com seu conhecimento geral e deixe claro "
    "que a resposta não veio dos documentos dele."
)


class RAGService:
    def __init__(
        self,
        chunk_repository: DocumentChunkRepository,
        embedding_client: EmbeddingClient,
        llm_client: LLMClient,
    ) -> None:
        self._chunks = chunk_repository
        self._embeddings = embedding_client
        self._llm = llm_client

    async def answer(
        self, owner_id: UUID, conversation_history: list[Message], question: str
    ) -> tuple[str, list[MessageSource]]:
        settings = get_settings()

        [query_embedding] = await self._embeddings.embed([question])
        candidates = await self._chunks.search_similar(
            owner_id, query_embedding, settings.rag_retrieval_top_k
        )
        top_chunks = rerank(question, candidates, settings.rag_context_top_k)

        prompt = self._build_prompt(conversation_history, top_chunks, question)
        answer = await self._llm.generate_reply(prompt)

        sources = [
            MessageSource(
                document_id=rc.chunk.document_id,
                document_filename=rc.document_filename,
                chunk_index=rc.chunk.chunk_index,
                snippet=rc.chunk.content[:_SNIPPET_LENGTH],
            )
            for rc in top_chunks
        ]
        return answer, sources

    def _build_prompt(
        self, history: list[Message], top_chunks: list[RetrievedChunk], question: str
    ) -> list[ChatMessage]:
        if top_chunks:
            context = "\n\n".join(
                f"[Fonte {i + 1}: {rc.document_filename}, trecho {rc.chunk.chunk_index}]\n"
                f"{rc.chunk.content}"
                for i, rc in enumerate(top_chunks)
            )
            system_prompt = _SYSTEM_PROMPT_WITH_CONTEXT.format(context=context)
        else:
            system_prompt = _SYSTEM_PROMPT_NO_CONTEXT

        messages = [ChatMessage(role="system", content=system_prompt)]
        messages.extend(ChatMessage(role=m.role, content=m.content) for m in history)
        messages.append(ChatMessage(role="user", content=question))
        return messages

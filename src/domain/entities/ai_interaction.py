from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AiInteraction:
    """Registro de uma chamada ao LLM pra responder uma pergunta (RAG) — usado pelo
    painel administrativo (nº de perguntas, taxa de erro, custo estimado, modelos mais
    usados). Tokens e custo são estimados por heurística: nem Ollama nem OpenAI devolvem
    contagem real de tokens pro `LLMClient` deste projeto."""

    id: UUID
    owner_id: UUID
    conversation_id: UUID
    provider: str
    model: str
    prompt_tokens_estimate: int
    completion_tokens_estimate: int
    cost_estimate_usd: float
    duration_ms: float
    succeeded: bool
    created_at: datetime

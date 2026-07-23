from dataclasses import dataclass
from typing import Literal

ChatRole = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    """Mensagem passada pro LLM. Diferente de `Message` (domain/entities/conversation.py):
    essa não é persistida — existe só pra montar o prompt de uma chamada (pode incluir um
    'system' com instruções/contexto RAG, que nunca vira uma linha na tabela messages)."""

    role: ChatRole
    content: str

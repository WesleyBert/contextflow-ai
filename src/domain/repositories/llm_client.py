from typing import Protocol

from src.domain.entities.conversation import Message


class LLMClient(Protocol):
    """Porta para o provedor de IA (Ollama local ou OpenAI).

    A aplicação depende só disso — trocar de provedor é uma questão de
    configuração (AI_PROVIDER no .env), não de reescrever código.
    """

    async def generate_reply(self, history: list[Message]) -> str: ...

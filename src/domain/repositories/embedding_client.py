from typing import Protocol


class EmbeddingClient(Protocol):
    """Porta para gerar embeddings (Ollama local ou OpenAI), mesmo espírito do LLMClient."""

    async def embed(self, texts: list[str]) -> list[list[float]]: ...

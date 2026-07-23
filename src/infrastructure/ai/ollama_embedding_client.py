import httpx

from src.infrastructure.config import get_settings


class OllamaEmbeddingClient:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        settings = get_settings()
        payload = {"model": settings.ollama_embedding_model, "input": texts}

        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0) as client:
            response = await client.post("/api/embed", json=payload)
            response.raise_for_status()
            data = response.json()

        return list(data["embeddings"])

import httpx

from src.infrastructure.config import get_settings


class OpenAIEmbeddingClient:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        settings = get_settings()
        payload = {"model": settings.openai_embedding_model, "input": texts}
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}

        async with httpx.AsyncClient(base_url="https://api.openai.com/v1", timeout=60.0) as client:
            response = await client.post("/embeddings", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return [item["embedding"] for item in data["data"]]

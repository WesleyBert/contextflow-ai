import httpx

from src.domain.entities.conversation import Message
from src.infrastructure.config import get_settings


class OllamaLLMClient:
    async def generate_reply(self, history: list[Message]) -> str:
        settings = get_settings()
        payload = {
            "model": settings.ollama_model,
            "messages": [{"role": m.role, "content": m.content} for m in history],
            "stream": False,
        }

        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0) as client:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        return str(data["message"]["content"])

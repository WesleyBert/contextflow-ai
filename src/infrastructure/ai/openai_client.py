import httpx

from src.domain.entities.conversation import Message
from src.infrastructure.config import get_settings


class OpenAILLMClient:
    async def generate_reply(self, history: list[Message]) -> str:
        settings = get_settings()
        payload = {
            "model": settings.openai_model,
            "messages": [{"role": m.role, "content": m.content} for m in history],
        }
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}

        async with httpx.AsyncClient(base_url="https://api.openai.com/v1", timeout=60.0) as client:
            response = await client.post("/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return str(data["choices"][0]["message"]["content"])

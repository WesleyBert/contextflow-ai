from src.domain.repositories.llm_client import LLMClient
from src.infrastructure.ai.ollama_client import OllamaLLMClient
from src.infrastructure.ai.openai_client import OpenAILLMClient
from src.infrastructure.config import get_settings


def get_llm_client() -> LLMClient:
    """Strategy: escolhe a implementação de LLM conforme AI_PROVIDER no .env."""
    settings = get_settings()
    if settings.ai_provider == "openai":
        return OpenAILLMClient()
    return OllamaLLMClient()

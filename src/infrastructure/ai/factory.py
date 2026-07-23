from src.domain.repositories.embedding_client import EmbeddingClient
from src.domain.repositories.llm_client import LLMClient
from src.infrastructure.ai.ollama_client import OllamaLLMClient
from src.infrastructure.ai.ollama_embedding_client import OllamaEmbeddingClient
from src.infrastructure.ai.openai_client import OpenAILLMClient
from src.infrastructure.ai.openai_embedding_client import OpenAIEmbeddingClient
from src.infrastructure.config import get_settings


def get_llm_client() -> LLMClient:
    """Strategy: escolhe a implementação de LLM conforme AI_PROVIDER no .env."""
    settings = get_settings()
    if settings.ai_provider == "openai":
        return OpenAILLMClient()
    return OllamaLLMClient()


def get_embedding_client() -> EmbeddingClient:
    """Strategy: escolhe a implementação de embeddings conforme AI_PROVIDER no .env."""
    settings = get_settings()
    if settings.ai_provider == "openai":
        return OpenAIEmbeddingClient()
    return OllamaEmbeddingClient()

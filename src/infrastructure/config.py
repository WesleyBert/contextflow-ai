from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    secret_key: str = "changeme"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://contextflow:contextflow@localhost:5432/contextflow"

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "changeme"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    ai_provider: Literal["ollama", "openai"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # dimensão do vetor salvo no pgvector. nomic-embed-text (Ollama) = 768,
    # text-embedding-3-small (OpenAI) = 1536 — trocar de provedor exige nova
    # migration se a dimensão mudar (limitação conhecida, documentada no README).
    embedding_dim: int = 768

    upload_dir: str = "./uploads"
    max_upload_size_bytes: int = 20 * 1024 * 1024
    allowed_upload_content_types: tuple[str, ...] = (
        "application/pdf",
        "text/plain",
        "text/markdown",
    )

    chunk_size_chars: int = 800
    chunk_overlap_chars: int = 150
    rag_retrieval_top_k: int = 20
    rag_context_top_k: int = 5

    # janelas fixas (fixed window) contadas no Redis — protege login/registro contra
    # força bruta e upload contra abuso (cada upload dispara processamento de IA, que
    # custa tempo de CPU/GPU e, no caso do provedor OpenAI, dinheiro de verdade)
    rate_limit_auth_requests: int = 5
    rate_limit_auth_window_seconds: int = 60
    rate_limit_upload_requests: int = 10
    rate_limit_upload_window_seconds: int = 60

    # cache de respostas por Idempotency-Key (Redis) — evita reprocessar upload ou
    # rechamar o LLM se o cliente repetir a requisição com a mesma chave
    idempotency_ttl_seconds: int = 86400

    # preço por 1k tokens, usado só pra estimar custo no painel administrativo (não é
    # cobrança real). Zero por padrão porque o provedor padrão (Ollama) roda local e de
    # graça — configurar via .env pra refletir o preço do modelo OpenAI escolhido.
    token_price_per_1k_prompt_usd: float = 0.0
    token_price_per_1k_completion_usd: float = 0.0

    # e-mails com acesso ao painel administrativo (GET /admin/metrics), separados por
    # vírgula. Vazio por padrão — ninguém tem acesso até configurar explicitamente.
    admin_emails: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()

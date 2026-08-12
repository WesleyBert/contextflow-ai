from redis.asyncio import Redis

from src.infrastructure.rate_limit.redis_rate_limiter import redis_client

__all__ = ["RedisIdempotencyStore", "redis_client"]


class RedisIdempotencyStore:
    """Cache de respostas por chave de idempotência, com TTL — mesmo Redis já usado pelo
    rate limiter. Uma chave repetida dentro do TTL devolve a resposta cacheada em vez de
    reexecutar a operação (evita reprocessar upload ou chamar o LLM de novo num retry)."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        value = await self._client.get(f"idempotency:{key}")
        return str(value) if value is not None else None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        await self._client.set(f"idempotency:{key}", value, ex=ttl_seconds)

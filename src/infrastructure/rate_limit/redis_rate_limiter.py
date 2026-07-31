from redis.asyncio import Redis

from src.infrastructure.config import get_settings

redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)


class RedisRateLimiter:
    """Janela fixa contada no Redis: cada chave incrementa um contador que expira
    sozinho no fim da janela. Simples e suficiente aqui — não precisa da precisão de
    uma janela deslizante para proteger login/registro/upload contra abuso."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def check(self, key: str, limit: int, window_seconds: int) -> bool:
        redis_key = f"rate_limit:{key}"
        count = await self._client.incr(redis_key)
        if count == 1:
            await self._client.expire(redis_key, window_seconds)
        return count <= limit

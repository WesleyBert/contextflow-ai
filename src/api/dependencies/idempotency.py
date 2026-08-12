from src.domain.repositories.idempotency_store import IdempotencyStore
from src.infrastructure.idempotency.redis_idempotency_store import (
    RedisIdempotencyStore,
    redis_client,
)


def get_idempotency_store() -> IdempotencyStore:
    return RedisIdempotencyStore(redis_client)

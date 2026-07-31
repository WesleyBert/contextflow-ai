from typing import Annotated

from fastapi import Depends, Request

from src.api.dependencies.auth import get_current_user
from src.domain.entities.user import User
from src.domain.exceptions.base import RateLimitExceededError
from src.domain.repositories.rate_limiter import RateLimiter
from src.infrastructure.config import get_settings
from src.infrastructure.rate_limit.redis_rate_limiter import RedisRateLimiter, redis_client


def get_rate_limiter() -> RateLimiter:
    return RedisRateLimiter(redis_client)


async def rate_limit_auth(
    request: Request,
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Aplicada em /auth/register e /auth/login, por IP — cada rota com contador
    próprio (a chave inclui o path), pra não travar login de quem só errou o registro."""
    settings = get_settings()
    client_host = request.client.host if request.client else "unknown"
    key = f"{request.url.path}:{client_host}"

    allowed = await rate_limiter.check(
        key, settings.rate_limit_auth_requests, settings.rate_limit_auth_window_seconds
    )
    if not allowed:
        raise RateLimitExceededError("Muitas tentativas. Tente novamente em instantes.")


async def rate_limit_upload(
    current_user: Annotated[User, Depends(get_current_user)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Aplicada em POST /documents, por usuário — cada upload dispara processamento
    de IA (custa tempo de CPU/GPU e, com o provedor OpenAI, dinheiro de verdade)."""
    settings = get_settings()
    key = f"upload:{current_user.id}"

    allowed = await rate_limiter.check(
        key, settings.rate_limit_upload_requests, settings.rate_limit_upload_window_seconds
    )
    if not allowed:
        raise RateLimitExceededError("Muitos uploads. Tente novamente em instantes.")

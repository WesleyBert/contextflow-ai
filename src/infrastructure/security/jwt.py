from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast
from uuid import UUID

from jose import JWTError, jwt

from src.infrastructure.config import get_settings

ALGORITHM = "HS256"

TokenType = Literal["access", "refresh"]


def _create_token(user_id: UUID, token_type: TokenType, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return cast(str, jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM))


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    return _create_token(
        user_id, "access", timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )


def create_refresh_token(user_id: UUID) -> str:
    settings = get_settings()
    return _create_token(
        user_id, "refresh", timedelta(days=settings.jwt_refresh_token_expire_days)
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        return cast(dict[str, Any], decoded)
    except JWTError as exc:
        raise ValueError("Token inválido ou expirado") from exc

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.db import get_db
from src.application.services.auth_service import AuthService
from src.domain.entities.user import User
from src.domain.exceptions.base import UnauthorizedError
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.security.jwt import decode_token

_bearer_scheme = HTTPBearer()


def get_user_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return SqlAlchemyUserRepository(db)


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(user_repository)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Token não é um access token")

    user = await user_repository.get_by_id(UUID(payload["sub"]))
    if user is None:
        raise UnauthorizedError("Usuário do token não existe mais")

    return user

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.api.dependencies.auth import get_auth_service, get_current_user, get_user_repository
from src.api.dependencies.rate_limit import rate_limit_auth
from src.api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.application.services.auth_service import AuthService
from src.domain.entities.user import User
from src.domain.exceptions.base import UnauthorizedError
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.security.jwt import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_auth)],
)
async def register(
    body: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    return await auth_service.register_user(email=body.email, password=body.password)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_auth)])
async def login(
    body: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    user = await auth_service.authenticate_user(email=body.email, password=body.password)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Token não é um refresh token")

    user = await user_repository.get_by_id(UUID(payload["sub"]))
    if user is None:
        raise UnauthorizedError("Usuário do token não existe mais")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

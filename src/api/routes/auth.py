from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.dependencies.auth import get_auth_service, get_current_user
from src.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.application.services.auth_service import AuthService
from src.domain.entities.user import User
from src.infrastructure.security.jwt import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    return await auth_service.register_user(email=body.email, password=body.password)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    user = await auth_service.authenticate_user(email=body.email, password=body.password)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

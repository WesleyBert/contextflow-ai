from src.domain.entities.user import User
from src.domain.exceptions.base import AlreadyExistsError, UnauthorizedError
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.security.password import hash_password, verify_password


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def register_user(self, email: str, password: str) -> User:
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise AlreadyExistsError(f"Já existe um usuário com o e-mail {email}")

        return await self._users.create(email=email, hashed_password=hash_password(password))

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("E-mail ou senha inválidos")

        return user

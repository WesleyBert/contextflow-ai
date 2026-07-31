import pytest

from src.application.services.auth_service import AuthService
from src.domain.exceptions.base import AlreadyExistsError, UnauthorizedError
from src.infrastructure.security.password import verify_password
from tests.unit.repo_fakes import FakeUserRepository


@pytest.fixture
def auth_service() -> AuthService:
    return AuthService(FakeUserRepository())


async def test_register_user_hashes_password(auth_service: AuthService) -> None:
    user = await auth_service.register_user("ana@example.com", "senha12345")

    assert user.email == "ana@example.com"
    assert user.hashed_password != "senha12345"
    assert verify_password("senha12345", user.hashed_password)


async def test_register_user_raises_when_email_already_exists(auth_service: AuthService) -> None:
    await auth_service.register_user("ana@example.com", "senha12345")

    with pytest.raises(AlreadyExistsError):
        await auth_service.register_user("ana@example.com", "outra-senha")


async def test_authenticate_user_succeeds_with_correct_password(auth_service: AuthService) -> None:
    await auth_service.register_user("ana@example.com", "senha12345")

    user = await auth_service.authenticate_user("ana@example.com", "senha12345")

    assert user.email == "ana@example.com"


async def test_authenticate_user_raises_for_wrong_password(auth_service: AuthService) -> None:
    await auth_service.register_user("ana@example.com", "senha12345")

    with pytest.raises(UnauthorizedError):
        await auth_service.authenticate_user("ana@example.com", "senha-errada")


async def test_authenticate_user_raises_for_unknown_email(auth_service: AuthService) -> None:
    with pytest.raises(UnauthorizedError):
        await auth_service.authenticate_user("desconhecido@example.com", "senha12345")

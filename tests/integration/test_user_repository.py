from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository


async def test_create_and_get_by_email(db_session: AsyncSession) -> None:
    repository = SqlAlchemyUserRepository(db_session)

    user = await repository.create(email="ana@example.com", hashed_password="hash")

    fetched = await repository.get_by_email("ana@example.com")
    assert fetched is not None
    assert fetched.id == user.id


async def test_get_by_email_returns_none_when_missing(db_session: AsyncSession) -> None:
    repository = SqlAlchemyUserRepository(db_session)

    assert await repository.get_by_email("ninguem@example.com") is None


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repository = SqlAlchemyUserRepository(db_session)

    assert await repository.get_by_id(uuid4()) is None

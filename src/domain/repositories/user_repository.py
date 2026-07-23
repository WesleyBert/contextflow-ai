from typing import Protocol
from uuid import UUID

from src.domain.entities.user import User


class UserRepository(Protocol):
    """Contrato que a camada de aplicação usa para persistir/consultar usuários.

    A implementação de verdade (SQLAlchemy + Postgres) fica em
    infrastructure/repositories. Isso permite trocar a tecnologia de
    persistência, ou usar um repositório falso nos testes, sem tocar
    na lógica de negócio.
    """

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def create(self, email: str, hashed_password: str) -> User: ...

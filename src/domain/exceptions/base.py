class DomainError(Exception):
    """Erro base para regras de negócio violadas (não é um erro de infraestrutura)."""


class NotFoundError(DomainError):
    """Um recurso solicitado não existe."""


class AlreadyExistsError(DomainError):
    """Tentativa de criar um recurso que já existe (ex.: e-mail duplicado)."""


class UnauthorizedError(DomainError):
    """Usuário não autenticado ou credenciais inválidas."""


class ForbiddenError(DomainError):
    """Usuário autenticado, mas sem permissão para o recurso (ex.: documento de outro usuário)."""

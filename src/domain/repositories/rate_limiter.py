from typing import Protocol


class RateLimiter(Protocol):
    """Porta para controle de taxa de requisições. A implementação de verdade (Redis)
    fica em infrastructure/rate_limit — permite trocar por outro backend, ou usar um
    limitador falso nos testes, sem tocar na lógica de negócio."""

    async def check(self, key: str, limit: int, window_seconds: int) -> bool:
        """Registra uma requisição sob `key` e devolve True se ela pode prosseguir,
        ou False se o limite de `limit` requisições na janela de `window_seconds` já
        foi atingido."""
        ...

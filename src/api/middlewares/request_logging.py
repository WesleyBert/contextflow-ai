import logging
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.infrastructure.logging import request_id_var

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """ASGI puro (não `BaseHTTPMiddleware`) de propósito: `BaseHTTPMiddleware` bufferiza
    a resposta pra poder inspecioná-la, o que quebra streaming — e a rota de SSE
    (`/documents/{id}/status/stream`) depende de streaming de verdade. Aqui só
    envelopamos `send`, então cada mensagem ASGI (inclusive cada chunk do SSE) continua
    passando direto."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._resolve_request_id(scope)
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                headers.append("x-request-id", request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "request completed",
                extra={
                    "request_id": request_id,
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            request_id_var.reset(token)

    @staticmethod
    def _resolve_request_id(scope: Scope) -> str:
        headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        for name, value in headers:
            if name == b"x-request-id":
                return value.decode("latin-1")
        return str(uuid.uuid4())

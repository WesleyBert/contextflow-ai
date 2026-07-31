"""Logging estruturado (uma linha JSON por evento) pra API e worker.

Não usa nenhuma lib externa (structlog, python-json-logger) — é só um Formatter que
serializa o LogRecord, mais um Filter que injeta o `request_id` da requisição atual via
contextvar. Como todo logger filho propaga pro root por padrão, isso vale automaticamente
pra qualquer `logging.getLogger(__name__)` do projeto — inclusive o `sqlalchemy.engine`
(usado pelo `echo=True` do engine em desenvolvimento), sem precisar tocar nesse código.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_STANDARD_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}

_HANDLER_MARKER = "_contextflow_structured_handler"


class RequestIdFilter(logging.Filter):
    """Injeta o request_id da requisição em andamento (se houver) em todo LogRecord,
    pra não precisar passar `extra={"request_id": ...}` manualmente em cada log."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS and value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdFilter())
    setattr(handler, _HANDLER_MARKER, True)

    root.addHandler(handler)
    root.setLevel(level)

    # uvicorn já loga cada requisição no formato de texto padrão dele; a requisição
    # completa também vira uma linha JSON estruturada pelo nosso próprio middleware
    # (`api/middlewares/request_logging.py`), então o access log embutido só duplicaria
    # a mesma informação com menos contexto (sem request_id, duration_ms etc.).
    logging.getLogger("uvicorn.access").disabled = True

    # O engine do SQLAlchemy (`echo=True` em desenvolvimento) anexa seu próprio handler de
    # texto puro nesse logger na hora em que é criado, *se* o logger ainda não tiver nenhum
    # handler (`if not self.logger.handlers: ...` — lógica interna do SQLAlchemy). A ordem
    # de import varia: na API o engine já existe quando chegamos aqui (import por trás dos
    # routers, antes de create_app() chamar essa função); no worker Celery é o contrário —
    # celery_app.py chama isso antes de tasks.py (via `include=[...]`) importar session.py,
    # então o engine só nasce depois. Um NullHandler cobre os dois casos: satisfaz o `if not
    # self.logger.handlers` do SQLAlchemy (não anexa nada de novo mais tarde) e, se ele já
    # tinha anexado o próprio handler antes, esse `clear()` remove. O propagate continua
    # ligado, então o registro sempre chega no nosso handler do root, formatado em JSON.
    sqlalchemy_engine_logger = logging.getLogger("sqlalchemy.engine.Engine")
    sqlalchemy_engine_logger.handlers.clear()
    sqlalchemy_engine_logger.addHandler(logging.NullHandler())

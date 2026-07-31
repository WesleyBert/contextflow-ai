import json
import logging
import sys

from src.infrastructure.logging import JsonFormatter, RequestIdFilter, request_id_var


def _make_record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="teste",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="mensagem de teste",
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_formatter_produces_valid_json_with_expected_fields() -> None:
    record = _make_record()

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "teste"
    assert payload["message"] == "mensagem de teste"
    assert "timestamp" in payload


def test_json_formatter_includes_extra_fields() -> None:
    record = _make_record(document_id="abc-123", duration_ms=42.5)

    payload = json.loads(JsonFormatter().format(record))

    assert payload["document_id"] == "abc-123"
    assert payload["duration_ms"] == 42.5


def test_json_formatter_includes_exception_info() -> None:
    try:
        raise ValueError("algo deu errado")
    except ValueError:
        record = _make_record()
        record.exc_info = sys.exc_info()

    payload = json.loads(JsonFormatter().format(record))

    assert "ValueError" in payload["exc_info"]
    assert "algo deu errado" in payload["exc_info"]


def test_request_id_filter_injects_contextvar_value() -> None:
    token = request_id_var.set("req-abc-123")
    try:
        record = _make_record()
        RequestIdFilter().filter(record)
        assert record.request_id == "req-abc-123"  # type: ignore[attr-defined]
    finally:
        request_id_var.reset(token)


def test_request_id_filter_does_not_override_explicit_value() -> None:
    token = request_id_var.set("req-do-contexto")
    try:
        record = _make_record(request_id="req-explicito")
        RequestIdFilter().filter(record)
        assert record.request_id == "req-explicito"  # type: ignore[attr-defined]
    finally:
        request_id_var.reset(token)


def test_request_id_filter_yields_none_outside_a_request() -> None:
    record = _make_record()
    RequestIdFilter().filter(record)
    assert record.request_id is None  # type: ignore[attr-defined]

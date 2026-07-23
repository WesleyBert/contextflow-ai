from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.base import (
    AlreadyExistsError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

_STATUS_BY_EXCEPTION = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    AlreadyExistsError: status.HTTP_409_CONFLICT,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
}


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"message": message}})


def register_exception_handlers(app: FastAPI) -> None:
    for exception_type, status_code in _STATUS_BY_EXCEPTION.items():

        def _handler(
            _request: Request, exc: Exception, status_code: int = status_code
        ) -> JSONResponse:
            return _error_response(status_code, str(exc))

        app.add_exception_handler(exception_type, _handler)

    def _unhandled_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Erro interno do servidor")

    app.add_exception_handler(Exception, _unhandled_error_handler)

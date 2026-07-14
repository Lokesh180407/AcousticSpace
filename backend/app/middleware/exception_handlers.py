from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _json_error(status_code: int, code: str, message: str, path: str | None = None):
    payload = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if path:
        payload["error"]["path"] = path
    return JSONResponse(status_code=status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _json_error(422, "VALIDATION_ERROR", "Request validation failed", request.url.path)


async def generic_exception_handler(request: Request, exc: Exception):
    return _json_error(500, "INTERNAL_SERVER_ERROR", "Unexpected server error", request.url.path)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


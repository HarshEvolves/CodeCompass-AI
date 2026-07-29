"""
Global Exception Handlers (Phase 9).

Registers application-wide exception handlers on the FastAPI app so that
every error response follows the standard format defined in responses.py.

Handles:
  1. HTTPException        → maps to standard error with appropriate error code
  2. RequestValidationError → 422 with VALIDATION_ERROR code + field details
  3. Exception (catch-all)  → 500 with INTERNAL_SERVER_ERROR, logs traceback

These handlers replace FastAPI's default error responses without touching
any individual route logic.
"""

import traceback
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_codes import ErrorCode
from app.core.responses import build_error_response
from app.core.logging import logger


# ---------------------------------------------------------------------------
# Mapping: HTTP status code → error code constant
# ---------------------------------------------------------------------------

_STATUS_TO_ERROR_CODE = {
    400: ErrorCode.VALIDATION_ERROR,
    401: ErrorCode.AUTHENTICATION_REQUIRED,
    403: ErrorCode.AUTHENTICATION_REQUIRED,
    404: ErrorCode.RESOURCE_NOT_FOUND,
    405: ErrorCode.METHOD_NOT_SUPPORTED,
    409: ErrorCode.DUPLICATE_RESOURCE,
    422: ErrorCode.VALIDATION_ERROR,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}


def _error_code_for_status(status_code: int) -> str:
    """Returns the error code constant for a given HTTP status, with a fallback."""
    return _STATUS_TO_ERROR_CODE.get(status_code, ErrorCode.INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 1. HTTPException handler
# ---------------------------------------------------------------------------

async def http_exception_handler(request, exc: StarletteHTTPException):
    """
    Catches all HTTPException instances raised in routes or dependencies
    and returns a standard error JSON response.
    """
    # Derive error code from status code, but use specific codes for known messages
    error_code = _error_code_for_status(exc.status_code)

    # Use more specific error codes for certain detail messages
    detail_str = str(exc.detail) if exc.detail else ""
    if "Token has expired" in detail_str:
        error_code = ErrorCode.TOKEN_EXPIRED
    elif "already registered" in detail_str:
        error_code = ErrorCode.DUPLICATE_RESOURCE
    elif "not supported" in detail_str:
        error_code = ErrorCode.METHOD_NOT_SUPPORTED
    elif "Invalid email or password" in detail_str or "Could not validate credentials" in detail_str:
        error_code = ErrorCode.INVALID_CREDENTIALS

    logger.warning(
        "HTTP error",
        extra={
            "status_code": exc.status_code,
            "error_code": error_code,
            "detail": detail_str,
            "path": str(request.url.path),
            "method": request.method,
        },
    )

    body = build_error_response(
        code=error_code,
        message=detail_str,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers=getattr(exc, "headers", None),
    )


# ---------------------------------------------------------------------------
# 2. RequestValidationError handler (422)
# ---------------------------------------------------------------------------

async def validation_exception_handler(request, exc: RequestValidationError):
    """
    Catches Pydantic / FastAPI validation errors and returns a 422 response
    with structured field-level error details.
    """
    # Build a simplified list of field errors
    field_errors = []
    for error in exc.errors():
        field_errors.append({
            "field": " → ".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", ""),
            "type": error.get("type", ""),
        })

    logger.warning(
        "Validation error",
        extra={
            "status_code": 422,
            "error_code": ErrorCode.VALIDATION_ERROR,
            "path": str(request.url.path),
            "method": request.method,
        },
    )

    body = build_error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        details=field_errors,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=body,
    )


# ---------------------------------------------------------------------------
# 3. Catch-all unhandled exception handler (500)
# ---------------------------------------------------------------------------

async def unhandled_exception_handler(request, exc: Exception):
    """
    Last-resort handler for unexpected exceptions.
    Logs the full traceback and returns a generic 500 response.
    In debug mode, the traceback is included in the response details.
    """
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)

    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "status_code": 500,
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
            "path": str(request.url.path),
            "method": request.method,
        },
        exc_info=True,
    )

    # Import settings here to check DEBUG flag (avoids circular imports at module level)
    from app.core.config import settings

    details = "".join(tb) if settings.DEBUG else None

    body = build_error_response(
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        details=details,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=body,
    )


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """
    Call this once during app startup to register all global exception handlers.
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

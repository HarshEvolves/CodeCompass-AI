"""
Reusable Error Codes (Phase 9).

Centralized constants for all application error codes.
Using these constants ensures consistency across exception handlers,
API routes, and error responses — no more scattered hardcoded strings.

Usage:
    from app.core.error_codes import ErrorCode
    raise HTTPException(..., detail=ErrorCode.RESOURCE_NOT_FOUND)
"""


class ErrorCode:
    """
    Namespace for all application error code constants.
    Each code is a short, uppercase string describing the error category.
    """

    # --- Authentication & Authorization ----------------------------------------
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # --- Resource Errors -------------------------------------------------------
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"

    # --- Validation ------------------------------------------------------------
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # --- Business Logic --------------------------------------------------------
    METHOD_NOT_SUPPORTED = "METHOD_NOT_SUPPORTED"

    # --- Server Errors ---------------------------------------------------------
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

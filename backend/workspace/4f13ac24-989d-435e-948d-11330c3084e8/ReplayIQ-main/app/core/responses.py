"""
Standard API Response Schemas (Phase 9).

Defines a consistent error response format that all exception handlers use.
Success responses continue to use their existing Pydantic response_model shapes;
only error responses are wrapped in this standard format.

Standard error response shape:
{
    "success": false,
    "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Project not found",
        "details": null
    }
}
"""

from typing import Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Inner error object containing the machine-readable code,
    human-readable message, and optional structured details.
    """
    code: str = Field(description="Machine-readable error code (e.g. VALIDATION_ERROR)")
    message: str = Field(description="Human-readable error description")
    details: Any = Field(default=None, description="Optional extra context (validation field errors, etc.)")


class ErrorResponse(BaseModel):
    """
    Top-level error response envelope.
    Returned by all global exception handlers.
    """
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorDetail


def build_error_response(code: str, message: str, details: Any = None) -> dict:
    """
    Helper that constructs a standard error response dict
    ready to be returned from a JSONResponse.
    """
    return ErrorResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details),
    ).model_dump()

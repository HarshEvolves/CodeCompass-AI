"""
Pydantic schemas for the Analytics API (Phase 8).

Defines the structured JSON responses returned by each analytics endpoint.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/analytics/summary
# ---------------------------------------------------------------------------

class SummaryResponse(BaseModel):
    """
    Aggregate statistics across all API logs in a project.
    """
    total_requests: int = Field(
        description="Total number of logged API requests"
    )
    successful_requests: int = Field(
        description="Count of requests with a 2xx status code"
    )
    failed_requests: int = Field(
        description="Count of requests with a 4xx or 5xx status code"
    )
    average_response_time_ms: float | None = Field(
        description="Mean response time in milliseconds (None if no logs exist)"
    )
    slowest_request_ms: int | None = Field(
        description="Maximum response time in milliseconds (None if no logs exist)"
    )
    fastest_request_ms: int | None = Field(
        description="Minimum response time in milliseconds (None if no logs exist)"
    )


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/analytics/methods
# ---------------------------------------------------------------------------

class MethodCountsResponse(BaseModel):
    """
    Request counts grouped by HTTP method (GET, POST, PUT, etc.).
    Returned as a dynamic dict so any method name is a valid key.
    """
    counts: dict[str, int] = Field(
        description="Map of HTTP method → request count"
    )


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/analytics/status-codes
# ---------------------------------------------------------------------------

class StatusCodeCountsResponse(BaseModel):
    """
    Request counts grouped by HTTP status code.
    Keys are stringified status codes (e.g. '200', '404').
    """
    counts: dict[str, int] = Field(
        description="Map of status code → request count"
    )


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/analytics/slow-requests
# ---------------------------------------------------------------------------

class SlowRequestItem(BaseModel):
    """
    A single API log entry included in the slow-requests listing.
    """
    id: uuid.UUID
    method: str
    url: str
    status_code: int
    response_time_ms: int
    created_at: datetime

    # Allow reading attributes directly from SQLAlchemy model instances
    model_config = ConfigDict(from_attributes=True)


class SlowRequestsResponse(BaseModel):
    """
    Wrapper containing a list of the slowest requests, ordered by
    response_time_ms descending.
    """
    requests: list[SlowRequestItem] = Field(
        description="Slowest API log entries, ordered by response time (descending)"
    )

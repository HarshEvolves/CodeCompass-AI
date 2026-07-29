"""
Pydantic schemas for the Response Comparison Engine (Phase 7).

Defines the structured JSON response returned when comparing
an original ApiLog with its Replay result.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-comparison schemas — one for each dimension we compare
# ---------------------------------------------------------------------------

class StatusComparison(BaseModel):
    """Compares the HTTP status codes between original and replay."""
    old_status: int | None = Field(
        description="HTTP status code from the original API log"
    )
    new_status: int | None = Field(
        description="HTTP status code from the replay"
    )
    status_changed: bool = Field(
        description="True if the status codes differ"
    )


class HeadersComparison(BaseModel):
    """Compares response headers between original and replay (order-insensitive)."""
    headers_changed: bool = Field(
        description="True if there is any difference in the response headers"
    )


class BodyComparison(BaseModel):
    """
    Compares JSON response bodies between original and replay.
    Also provides field-level diffs when both sides are JSON objects.
    """
    body_changed: bool = Field(
        description="True if the response bodies differ"
    )
    added_fields: list[str] = Field(
        default_factory=list,
        description="Top-level keys present in the replay but not in the original"
    )
    removed_fields: list[str] = Field(
        default_factory=list,
        description="Top-level keys present in the original but not in the replay"
    )
    modified_fields: list[str] = Field(
        default_factory=list,
        description="Top-level keys present in both but with different values"
    )


class ResponseTimeComparison(BaseModel):
    """Compares response latency between original and replay."""
    old_response_time_ms: int | None = Field(
        description="Response time (ms) from the original API log"
    )
    new_response_time_ms: int | None = Field(
        description="Response time (ms) from the replay"
    )
    latency_difference_ms: int | None = Field(
        description="Difference: new - old (positive means slower replay)"
    )


# ---------------------------------------------------------------------------
# Top-level comparison response
# ---------------------------------------------------------------------------

class ComparisonResponse(BaseModel):
    """
    Full comparison result combining all dimensions.
    Returned by GET /projects/{project_id}/logs/{log_id}/replays/{replay_id}/comparison
    """
    status: StatusComparison
    headers: HeadersComparison
    body: BodyComparison
    response_time: ResponseTimeComparison
    overall_changed: bool = Field(
        description="True if ANY of the sub-comparisons detected a difference"
    )

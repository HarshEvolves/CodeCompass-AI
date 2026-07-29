"""
Analytics Service (Phase 8) — API Log Analytics.

Provides analytics queries for API logs within a project.
Uses SQLAlchemy aggregate functions (func.count, func.avg, func.max, func.min)
to push computation down to PostgreSQL rather than loading all rows into Python.

All methods are static, matching the pattern used by ProjectService, LogService, etc.
"""

import uuid
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.api_log import ApiLog
from app.schemas.analytics import (
    SummaryResponse,
    MethodCountsResponse,
    StatusCodeCountsResponse,
    SlowRequestItem,
    SlowRequestsResponse,
)


class AnalyticsService:
    """
    Stateless service providing analytics queries on API log data.
    All heavy computation is done in SQL via aggregate functions.
    """

    # ------------------------------------------------------------------
    # 1. Summary Statistics
    # ------------------------------------------------------------------
    @staticmethod
    def get_summary(db: Session, project_id: uuid.UUID) -> SummaryResponse:
        """
        Returns aggregate stats for all API logs in the project:
          - total_requests
          - successful_requests  (2xx status codes)
          - failed_requests      (4xx + 5xx status codes)
          - average_response_time_ms
          - slowest_request_ms
          - fastest_request_ms

        Uses a single SQL query with conditional counting via case().
        """
        # Build a single aggregate query instead of multiple round-trips
        result = db.query(
            func.count(ApiLog.id).label("total"),
            func.count(
                func.nullif(
                    # nullif returns NULL when the condition is false,
                    # so count() skips those rows
                    ApiLog.status_code < 300,  # 2xx = codes 200-299
                    False,
                )
            ).label("successful"),
            func.count(
                func.nullif(
                    ApiLog.status_code >= 400,  # 4xx + 5xx = codes >= 400
                    False,
                )
            ).label("failed"),
            func.avg(ApiLog.response_time_ms).label("avg_time"),
            func.max(ApiLog.response_time_ms).label("max_time"),
            func.min(ApiLog.response_time_ms).label("min_time"),
        ).filter(
            ApiLog.project_id == project_id
        ).one()

        return SummaryResponse(
            total_requests=result.total,
            successful_requests=result.successful,
            failed_requests=result.failed,
            # Round average to 2 decimal places for readability
            average_response_time_ms=(
                round(float(result.avg_time), 2) if result.avg_time is not None else None
            ),
            slowest_request_ms=result.max_time,
            fastest_request_ms=result.min_time,
        )

    # ------------------------------------------------------------------
    # 2. Method Counts
    # ------------------------------------------------------------------
    @staticmethod
    def get_method_counts(db: Session, project_id: uuid.UUID) -> MethodCountsResponse:
        """
        Returns request counts grouped by HTTP method.
        Example: {"GET": 15, "POST": 10}

        Uses SQL GROUP BY to avoid loading individual rows.
        """
        rows = db.query(
            ApiLog.method,
            func.count(ApiLog.id).label("count"),
        ).filter(
            ApiLog.project_id == project_id
        ).group_by(
            ApiLog.method
        ).all()

        # Convert list of (method, count) tuples to a dict
        counts = {row.method: row.count for row in rows}

        return MethodCountsResponse(counts=counts)

    # ------------------------------------------------------------------
    # 3. Status Code Counts
    # ------------------------------------------------------------------
    @staticmethod
    def get_status_code_counts(db: Session, project_id: uuid.UUID) -> StatusCodeCountsResponse:
        """
        Returns request counts grouped by HTTP status code.
        Example: {"200": 25, "404": 2, "500": 4}

        Keys are stringified integers so the JSON output matches the spec.
        """
        rows = db.query(
            ApiLog.status_code,
            func.count(ApiLog.id).label("count"),
        ).filter(
            ApiLog.project_id == project_id
        ).group_by(
            ApiLog.status_code
        ).all()

        # Convert to {string_code: count} dict
        counts = {str(row.status_code): row.count for row in rows}

        return StatusCodeCountsResponse(counts=counts)

    # ------------------------------------------------------------------
    # 4. Slow Requests
    # ------------------------------------------------------------------
    @staticmethod
    def get_slow_requests(
        db: Session,
        project_id: uuid.UUID,
        limit: int = 10,
    ) -> SlowRequestsResponse:
        """
        Returns the slowest API logs ordered by response_time_ms descending.
        The `limit` parameter controls how many results are returned (default 10).

        Only fetches the columns needed for the response to keep the query lean.
        """
        logs = db.query(ApiLog).filter(
            ApiLog.project_id == project_id
        ).order_by(
            ApiLog.response_time_ms.desc()
        ).limit(limit).all()

        # Map ORM objects to Pydantic schemas
        items = [SlowRequestItem.model_validate(log) for log in logs]

        return SlowRequestsResponse(requests=items)

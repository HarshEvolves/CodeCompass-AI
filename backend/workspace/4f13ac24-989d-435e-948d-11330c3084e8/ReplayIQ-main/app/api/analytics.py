"""
API router for the Analytics API (Phase 8).

Exposes four read-only endpoints under /projects/{project_id}/analytics/:
  - GET /summary         → Aggregate statistics
  - GET /methods         → Counts by HTTP method
  - GET /status-codes    → Counts by status code
  - GET /slow-requests   → Slowest requests (configurable limit)

Every endpoint authenticates the user and verifies project ownership
before delegating to AnalyticsService.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.project_service import ProjectService
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    SummaryResponse,
    MethodCountsResponse,
    StatusCodeCountsResponse,
    SlowRequestsResponse,
)

router = APIRouter(
    prefix="/projects/{project_id}/analytics",
    tags=["analytics"],
)


# ---------------------------------------------------------------------------
# Helper: verify project ownership (reused by every endpoint)
# ---------------------------------------------------------------------------

def _verify_project(db: Session, project_id: uuid.UUID, user: User):
    """
    Checks that the project exists and belongs to the authenticated user.
    Raises 404 if not found.
    """
    project = ProjectService.get_project_by_id(db, project_id, user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


# ---------------------------------------------------------------------------
# 1. Summary Statistics
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
def get_summary(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns aggregate statistics for all API logs in the project:
    total requests, success/failure counts, and response-time metrics.
    """
    _verify_project(db, project_id, current_user)
    return AnalyticsService.get_summary(db, project_id)


# ---------------------------------------------------------------------------
# 2. Method Counts
# ---------------------------------------------------------------------------

@router.get("/methods", response_model=MethodCountsResponse, status_code=status.HTTP_200_OK)
def get_method_counts(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the number of API log entries grouped by HTTP method.
    """
    _verify_project(db, project_id, current_user)
    return AnalyticsService.get_method_counts(db, project_id)


# ---------------------------------------------------------------------------
# 3. Status Code Counts
# ---------------------------------------------------------------------------

@router.get("/status-codes", response_model=StatusCodeCountsResponse, status_code=status.HTTP_200_OK)
def get_status_code_counts(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the number of API log entries grouped by HTTP status code.
    """
    _verify_project(db, project_id, current_user)
    return AnalyticsService.get_status_code_counts(db, project_id)


# ---------------------------------------------------------------------------
# 4. Slow Requests
# ---------------------------------------------------------------------------

@router.get("/slow-requests", response_model=SlowRequestsResponse, status_code=status.HTTP_200_OK)
def get_slow_requests(
    project_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=100, description="Number of slow requests to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the slowest API log entries ordered by response_time_ms descending.
    Use the `limit` query parameter to control how many results are returned (1–100).
    """
    _verify_project(db, project_id, current_user)
    return AnalyticsService.get_slow_requests(db, project_id, limit=limit)

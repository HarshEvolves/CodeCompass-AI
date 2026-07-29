"""
Tests for the Analytics API (Phase 8).

Covers:
  - Summary statistics (total, success, failure, avg/max/min response time)
  - Method counts (grouped by HTTP verb)
  - Status code counts (grouped by status code)
  - Slow request ordering (descending by response_time_ms)
  - Empty project (no logs → safe zero/null results)
  - Unauthorized access (no token → 401)
"""

import uuid
import pytest
from fastapi import status

from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.api_log import ApiLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user_and_project(db_session):
    """Creates an authenticated user + project and returns (project, auth_headers)."""
    hashed_pass = get_password_hash("password123")
    user = User(
        full_name="Analytics User",
        email="analytics@example.com",
        hashed_password=hashed_pass,
    )
    db_session.add(user)
    db_session.commit()

    project = Project(name="Analytics Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}
    return project, headers


def _create_logs(db_session, project_id, logs_data: list[dict]):
    """
    Bulk-creates ApiLog entries for a project.
    Each item in logs_data is a dict with keys:
      method, url, status_code, response_time_ms
    """
    for entry in logs_data:
        log = ApiLog(
            project_id=project_id,
            method=entry["method"],
            url=entry.get("url", "http://api.example.com/test"),
            request_headers={},
            response_headers={},
            status_code=entry["status_code"],
            response_time_ms=entry["response_time_ms"],
        )
        db_session.add(log)
    db_session.commit()


# ---------------------------------------------------------------------------
# Sample dataset used by most tests
# ---------------------------------------------------------------------------

SAMPLE_LOGS = [
    {"method": "GET",    "status_code": 200, "response_time_ms": 50},
    {"method": "GET",    "status_code": 200, "response_time_ms": 80},
    {"method": "GET",    "status_code": 404, "response_time_ms": 30},
    {"method": "POST",   "status_code": 201, "response_time_ms": 120},
    {"method": "POST",   "status_code": 500, "response_time_ms": 200},
    {"method": "PUT",    "status_code": 200, "response_time_ms": 60},
    {"method": "DELETE", "status_code": 204, "response_time_ms": 40},
]


# ===========================================================================
# 1. Summary Statistics
# ===========================================================================

def test_summary_statistics(client, db_session):
    """
    Verifies that the /analytics/summary endpoint returns correct
    aggregate values for a known set of API logs.
    """
    project, headers = _create_user_and_project(db_session)
    _create_logs(db_session, project.id, SAMPLE_LOGS)

    response = client.get(
        f"/projects/{project.id}/analytics/summary",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Total: 7 logs
    assert data["total_requests"] == 7

    # Successful (2xx): 200, 200, 201, 200, 204 → 5
    assert data["successful_requests"] == 5

    # Failed (4xx+5xx): 404, 500 → 2
    assert data["failed_requests"] == 2

    # Response times: [50, 80, 30, 120, 200, 60, 40]
    assert data["slowest_request_ms"] == 200
    assert data["fastest_request_ms"] == 30

    # Average: (50+80+30+120+200+60+40) / 7 = 580/7 ≈ 82.86
    assert data["average_response_time_ms"] is not None
    assert abs(data["average_response_time_ms"] - 82.86) < 0.1


# ===========================================================================
# 2. Method Counts
# ===========================================================================

def test_method_counts(client, db_session):
    """
    Verifies that /analytics/methods returns correct per-method counts.
    """
    project, headers = _create_user_and_project(db_session)
    _create_logs(db_session, project.id, SAMPLE_LOGS)

    response = client.get(
        f"/projects/{project.id}/analytics/methods",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    counts = response.json()["counts"]

    # GET: 3, POST: 2, PUT: 1, DELETE: 1
    assert counts["GET"] == 3
    assert counts["POST"] == 2
    assert counts["PUT"] == 1
    assert counts["DELETE"] == 1


# ===========================================================================
# 3. Status Code Counts
# ===========================================================================

def test_status_code_counts(client, db_session):
    """
    Verifies that /analytics/status-codes returns correct per-code counts.
    """
    project, headers = _create_user_and_project(db_session)
    _create_logs(db_session, project.id, SAMPLE_LOGS)

    response = client.get(
        f"/projects/{project.id}/analytics/status-codes",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    counts = response.json()["counts"]

    # 200: 3 (GET×2 + PUT), 201: 1, 204: 1, 404: 1, 500: 1
    assert counts["200"] == 3
    assert counts["201"] == 1
    assert counts["204"] == 1
    assert counts["404"] == 1
    assert counts["500"] == 1


# ===========================================================================
# 4. Slow Request Ordering
# ===========================================================================

def test_slow_requests_ordering(client, db_session):
    """
    Verifies that /analytics/slow-requests returns logs sorted by
    response_time_ms descending and respects the limit parameter.
    """
    project, headers = _create_user_and_project(db_session)
    _create_logs(db_session, project.id, SAMPLE_LOGS)

    # Request top 3 slowest
    response = client.get(
        f"/projects/{project.id}/analytics/slow-requests?limit=3",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    items = response.json()["requests"]

    # Should return exactly 3 items
    assert len(items) == 3

    # Verify descending order
    times = [item["response_time_ms"] for item in items]
    assert times == sorted(times, reverse=True)

    # The slowest should be 200ms (POST /500), then 120ms (POST /201), then 80ms (GET /200)
    assert times[0] == 200
    assert times[1] == 120
    assert times[2] == 80


# ===========================================================================
# 5. Empty Project (no logs)
# ===========================================================================

def test_empty_project_summary(client, db_session):
    """
    Verifies that analytics endpoints return safe zero/null values
    when the project has no API logs.
    """
    project, headers = _create_user_and_project(db_session)
    # No logs created

    # Summary should return zeros and nulls
    response = client.get(
        f"/projects/{project.id}/analytics/summary",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_requests"] == 0
    assert data["successful_requests"] == 0
    assert data["failed_requests"] == 0
    assert data["average_response_time_ms"] is None
    assert data["slowest_request_ms"] is None
    assert data["fastest_request_ms"] is None


def test_empty_project_methods(client, db_session):
    """
    Methods endpoint should return an empty dict for a project with no logs.
    """
    project, headers = _create_user_and_project(db_session)

    response = client.get(
        f"/projects/{project.id}/analytics/methods",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["counts"] == {}


def test_empty_project_status_codes(client, db_session):
    """
    Status-codes endpoint should return an empty dict for a project with no logs.
    """
    project, headers = _create_user_and_project(db_session)

    response = client.get(
        f"/projects/{project.id}/analytics/status-codes",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["counts"] == {}


def test_empty_project_slow_requests(client, db_session):
    """
    Slow-requests endpoint should return an empty list for a project with no logs.
    """
    project, headers = _create_user_and_project(db_session)

    response = client.get(
        f"/projects/{project.id}/analytics/slow-requests",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["requests"] == []


# ===========================================================================
# 6. Unauthorized Access
# ===========================================================================

def test_unauthorized_summary(client):
    """Requesting /analytics/summary without auth returns 401."""
    response = client.get(f"/projects/{uuid.uuid4()}/analytics/summary")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_unauthorized_methods(client):
    """Requesting /analytics/methods without auth returns 401."""
    response = client.get(f"/projects/{uuid.uuid4()}/analytics/methods")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_unauthorized_status_codes(client):
    """Requesting /analytics/status-codes without auth returns 401."""
    response = client.get(f"/projects/{uuid.uuid4()}/analytics/status-codes")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_unauthorized_slow_requests(client):
    """Requesting /analytics/slow-requests without auth returns 401."""
    response = client.get(f"/projects/{uuid.uuid4()}/analytics/slow-requests")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

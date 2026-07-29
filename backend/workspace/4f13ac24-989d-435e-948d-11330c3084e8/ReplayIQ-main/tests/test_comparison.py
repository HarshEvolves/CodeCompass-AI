"""
Tests for the Response Comparison Engine (Phase 7).

Covers:
  - Status code changed / unchanged
  - Headers changed / unchanged
  - Body changed / unchanged (with field-level diff)
  - Response time difference
  - Unauthorized comparison (no token → 401)
  - Invalid replay ID (→ 404)
"""

import uuid
import pytest
from fastapi import status

from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.api_log import ApiLog
from app.models.replay import Replay


# ---------------------------------------------------------------------------
# Helper: creates user → project → log → replay chain in one call
# ---------------------------------------------------------------------------

def _create_test_data(
    db_session,
    *,
    # Original ApiLog fields
    original_status_code: int = 200,
    original_response_headers: dict | None = None,
    original_response_body: dict | None = None,
    original_response_time_ms: int = 100,
    # Replay fields
    replay_status_code: int | None = 200,
    replay_response_headers: dict | None = None,
    replay_response_body: dict | None = None,
    replay_response_time_ms: int | None = 120,
    replay_success: bool = True,
):
    """
    Creates a full ownership chain (user → project → log → replay)
    and returns all four objects plus an auth header dict.
    """
    # --- User ---
    hashed_pass = get_password_hash("password123")
    user = User(
        full_name="Test User",
        email="compare@example.com",
        hashed_password=hashed_pass,
    )
    db_session.add(user)
    db_session.commit()

    # --- Project ---
    project = Project(name="Comparison Test Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    # --- ApiLog ---
    log = ApiLog(
        project_id=project.id,
        method="GET",
        url="http://api.example.com/data",
        request_headers={"Accept": "application/json"},
        request_body=None,
        response_headers=original_response_headers or {"Content-Type": "application/json"},
        response_body=original_response_body or {"message": "ok"},
        status_code=original_status_code,
        response_time_ms=original_response_time_ms,
    )
    db_session.add(log)
    db_session.commit()

    # --- Replay ---
    replay = Replay(
        api_log_id=log.id,
        replay_status_code=replay_status_code,
        replay_response_headers=replay_response_headers or {"Content-Type": "application/json"},
        replay_response_body=replay_response_body or {"message": "ok"},
        replay_response_time_ms=replay_response_time_ms,
        replay_success=replay_success,
    )
    db_session.add(replay)
    db_session.commit()

    # --- Auth header ---
    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    return user, project, log, replay, headers


def _comparison_url(project_id, log_id, replay_id) -> str:
    """Builds the comparison endpoint URL."""
    return f"/projects/{project_id}/logs/{log_id}/replays/{replay_id}/comparison"


# ===========================================================================
# 1. Status Code — Changed
# ===========================================================================

def test_status_changed(client, db_session):
    """
    When original status is 200 and replay status is 500,
    the comparison should report status_changed = True.
    """
    _, project, log, replay, headers = _create_test_data(
        db_session,
        original_status_code=200,
        replay_status_code=500,
    )

    response = client.get(
        _comparison_url(project.id, log.id, replay.id),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"]["old_status"] == 200
    assert data["status"]["new_status"] == 500
    assert data["status"]["status_changed"] is True
    assert data["overall_changed"] is True


# ===========================================================================
# 2. Status Code — Unchanged
# ===========================================================================

def test_status_unchanged(client, db_session):
    """
    When both status codes are 200, status_changed should be False.
    """
    _, project, log, replay, headers = _create_test_data(
        db_session,
        original_status_code=200,
        replay_status_code=200,
    )

    response = client.get(
        _comparison_url(project.id, log.id, replay.id),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"]["old_status"] == 200
    assert data["status"]["new_status"] == 200
    assert data["status"]["status_changed"] is False


# ===========================================================================
# 3. Headers — Changed
# ===========================================================================

def test_headers_changed(client, db_session):
    """
    When response headers differ between original and replay,
    headers_changed should be True.
    """
    _, project, log, replay, headers = _create_test_data(
        db_session,
        original_response_headers={"Content-Type": "application/json"},
        replay_response_headers={"Content-Type": "text/html", "X-New": "value"},
    )

    response = client.get(
        _comparison_url(project.id, log.id, replay.id),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["headers"]["headers_changed"] is True
    assert data["overall_changed"] is True


# ===========================================================================
# 4. Headers — Unchanged
# ===========================================================================

def test_headers_unchanged(client, db_session):
    """
    When headers are identical (regardless of insertion order),
    headers_changed should be False.
    """
    _, project, log, replay, headers = _create_test_data(
        db_session,
        original_response_headers={"Content-Type": "application/json", "X-Req-Id": "42"},
        replay_response_headers={"X-Req-Id": "42", "Content-Type": "application/json"},
    )

    response = client.get(
        _comparison_url(project.id, log.id, replay.id),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["headers"]["headers_changed"] is False


# ===========================================================================
# 5. Body — Changed (with field-level diff)
# ===========================================================================

def test_body_changed(client, db_session):
    """
    When response bodies differ, body_changed should be True and
    field-level diff lists should be populated correctly.
    """
    _, project, log, replay, headers = _create_test_data(
        db_session,
        original_response_body={"message": "ok", "count": 5, "removed_key": "x"},
        replay_response_body={"message": "changed", "count": 5, "new_key": "y"},
    )

    response = client.get(
        _comparison_url(project.id, log.id, replay.id),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    body = data["body"]
    assert body["body_changed"] is True
    assert "new_key" in body["added_fields"]
    assert "removed_key" in body["removed_fields"]
    assert "message" in body["modified_fields"]
    # "count" is the same value → should NOT appear in modified_fields
    assert "count" not in body["modified_fields"]
    assert data["overall_changed"] is True


# ===========================================================================
# 6. Body — Unchanged
# ===========================================================================

def test_body_unchanged(client, db_session):
    """
    When response bodies are identical, body_changed should be False
    and all diff lists should be empty.
    """
    body = {"message": "ok", "items": [1, 2, 3]}
    _, project, log, replay, headers = _create_test_data(
        db_session,
        original_response_body=body,
        replay_response_body=body,
    )

    response = client.get(
        _comparison_url(project.id, log.id, replay.id),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["body"]["body_changed"] is False
    assert data["body"]["added_fields"] == []
    assert data["body"]["removed_fields"] == []
    assert data["body"]["modified_fields"] == []


# ===========================================================================
# 7. Response Time Difference
# ===========================================================================

def test_response_time_difference(client, db_session):
    """
    Verifies that the latency delta is computed correctly.
    old=100ms, new=250ms → diff=+150ms (replay was slower).
    """
    _, project, log, replay, headers = _create_test_data(
        db_session,
        original_response_time_ms=100,
        replay_response_time_ms=250,
    )

    response = client.get(
        _comparison_url(project.id, log.id, replay.id),
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    rt = data["response_time"]
    assert rt["old_response_time_ms"] == 100
    assert rt["new_response_time_ms"] == 250
    assert rt["latency_difference_ms"] == 150


# ===========================================================================
# 8. Unauthorized Comparison (no token)
# ===========================================================================

def test_unauthorized_comparison(client):
    """
    Requesting a comparison without an Authorization header should return 401.
    """
    url = _comparison_url(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ===========================================================================
# 9. Invalid Replay ID
# ===========================================================================

def test_invalid_replay_id(client, db_session):
    """
    Using a non-existent replay UUID should return 404 'Replay not found'.
    """
    _, project, log, _, headers = _create_test_data(db_session)

    # Use a random UUID that won't match any replay
    fake_replay_id = uuid.uuid4()
    response = client.get(
        _comparison_url(project.id, log.id, fake_replay_id),
        headers=headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["message"] == "Replay not found"
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

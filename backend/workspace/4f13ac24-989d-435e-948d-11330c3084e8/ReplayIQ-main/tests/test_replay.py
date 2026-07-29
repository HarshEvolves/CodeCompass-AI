import pytest
import uuid
import httpx
from fastapi import status
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.api_log import ApiLog
from app.models.replay import Replay

# Reusable mock response class
class MockResponse:
    def __init__(self, status_code=200, json_data=None, text_data=""):
        self.status_code = status_code
        self._json = json_data or {"message": "success"}
        self.headers = {"content-type": "application/json", "X-Custom": "custom-header-value"}
        self.text = text_data or '{"message": "success"}'

    def json(self):
        return self._json

def test_replay_unauthorized(client):
    """
    Verifies that triggering a replay without authorization token returns 401.
    """
    random_uuid1 = uuid.uuid4()
    random_uuid2 = uuid.uuid4()
    response = client.post(f"/projects/{random_uuid1}/logs/{random_uuid2}/replay")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_replay_non_existent_log(client, db_session):
    """
    Verifies that replaying a non-existent log or project returns 404.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Default Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Query details for non-existent log ID -> 404
    random_log_id = uuid.uuid4()
    response = client.post(f"/projects/{project.id}/logs/{random_log_id}/replay", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.anyio
async def test_successful_replay(client, db_session, monkeypatch):
    """
    Verifies a successful request replay, asserting return values and DB state.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Default Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    log = ApiLog(
        project_id=project.id,
        method="POST",
        url="http://api.example.com/test",
        request_headers={"Content-Type": "application/json"},
        request_body={"payload": "value"},
        response_headers={},
        status_code=200,
        response_time_ms=50
    )
    db_session.add(log)
    db_session.commit()

    # Mock AsyncClient.request to return successful response
    async def mock_request(*args, **kwargs):
        return MockResponse(status_code=200, json_data={"result": "replay-ok"})

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(f"/projects/{project.id}/logs/{log.id}/replay", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["replay_success"] is True
    assert data["replay_status_code"] == 200
    assert data["replay_response_body"] == {"result": "replay-ok"}
    assert data["api_log_id"] == str(log.id)
    assert data["error_message"] is None

    # Verify DB entry
    db_replay = db_session.query(Replay).filter(Replay.api_log_id == log.id).first()
    assert db_replay is not None
    assert db_replay.replay_success is True
    assert db_replay.replay_status_code == 200

@pytest.mark.anyio
async def test_replay_invalid_url(client, db_session, monkeypatch):
    """
    Verifies that replaying a log with a malformed url fails gracefully and logs the protocol error.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Default Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    log = ApiLog(
        project_id=project.id,
        method="GET",
        url="invalid_url_protocol",
        request_headers={},
        response_headers={},
        status_code=200,
        response_time_ms=50
    )
    db_session.add(log)
    db_session.commit()

    # Mock AsyncClient.request to raise UnsupportedProtocol error
    async def mock_request(*args, **kwargs):
        raise httpx.UnsupportedProtocol("Unsupported protocol error")

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(f"/projects/{project.id}/logs/{log.id}/replay", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["replay_success"] is False
    assert data["replay_status_code"] is None
    assert "Invalid URL" in data["error_message"]

@pytest.mark.anyio
async def test_replay_timeout(client, db_session, monkeypatch):
    """
    Verifies that a timeout failure logs the error gracefully.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Default Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    log = ApiLog(
        project_id=project.id,
        method="GET",
        url="http://api.example.com",
        request_headers={},
        response_headers={},
        status_code=200,
        response_time_ms=50
    )
    db_session.add(log)
    db_session.commit()

    # Mock timeout
    async def mock_request(*args, **kwargs):
        raise httpx.ConnectTimeout("Request timed out during connection")

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(f"/projects/{project.id}/logs/{log.id}/replay", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["replay_success"] is False
    assert "Connection Timeout" in data["error_message"]

@pytest.mark.anyio
async def test_replay_connection_failure(client, db_session, monkeypatch):
    """
    Verifies that connection refuse or DNS lookup failure logs the error gracefully.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Default Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    log = ApiLog(
        project_id=project.id,
        method="GET",
        url="http://non-existing-dns-name.xyz",
        request_headers={},
        response_headers={},
        status_code=200,
        response_time_ms=50
    )
    db_session.add(log)
    db_session.commit()

    # Mock connection failure
    async def mock_request(*args, **kwargs):
        raise httpx.ConnectError("DNS failure/connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(f"/projects/{project.id}/logs/{log.id}/replay", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["replay_success"] is False
    assert "Connection Failure" in data["error_message"]

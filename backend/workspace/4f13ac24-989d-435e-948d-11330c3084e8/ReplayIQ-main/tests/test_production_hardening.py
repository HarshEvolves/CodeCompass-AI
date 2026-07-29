import uuid
import pytest
import logging
from datetime import datetime, timezone
from fastapi import status
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.project import Project
from app.core.error_codes import ErrorCode
from app.core.logging import JSONFormatter

def test_user_registration_blank_name(client):
    """
    Verifies that a blank full_name is rejected during registration.
    """
    response = client.post(
        "/auth/register",
        json={"email": "blankname@example.com", "password": "securepassword", "full_name": "   "}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
    # Validate the structure of details is returned
    assert len(data["error"]["details"]) > 0
    assert "full_name" in data["error"]["details"][0]["field"]
    assert "Value error" in data["error"]["details"][0]["message"] or "blank" in data["error"]["details"][0]["message"]


def test_project_update_blank_name(client, db_session):
    """
    Verifies that a blank name is rejected during project update.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Project Active", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        f"/projects/{project.id}",
        json={"name": "   "},
        headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
    assert "name" in data["error"]["details"][0]["field"]


def test_api_log_invalid_url_format(client, db_session):
    """
    Verifies that malformed URLs are rejected when creating an API log.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Test Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "method": "POST",
        "url": "invalid_url_no_prefix",
        "status_code": 200,
        "response_time_ms": 100
    }

    response = client.post(f"/projects/{project.id}/logs", json=payload, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
    assert "url" in data["error"]["details"][0]["field"]


def test_method_not_allowed_exception_handler(client):
    """
    Verifies that a 405 Method Not Allowed error goes through the Starlette
    HTTPException handler and is correctly wrapped in the standard error format.
    """
    # Calling POST on GET-only /health route should trigger 405
    response = client.post("/health")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ErrorCode.METHOD_NOT_SUPPORTED
    assert "Method Not Allowed" in data["error"]["message"]


def test_unhandled_exception_handler(client, db_session, monkeypatch):
    """
    Verifies that a random crash in a route yields a 500 error in standard format.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Force a crash in the project creation service method
    from app.services.project_service import ProjectService
    def mock_create_project(*args, **kwargs):
        raise RuntimeError("Simulated Database Catastrophe")
    
    monkeypatch.setattr(ProjectService, "create_project", mock_create_project)

    response = client.post(
        "/projects",
        json={"name": "Crash Project", "description": "Crash Description"},
        headers=headers
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == ErrorCode.INTERNAL_SERVER_ERROR
    assert "unexpected error" in data["error"]["message"].lower()


def test_json_log_formatter():
    """
    Verifies the structured JSON formatter formats standard logs and uvicorn access logs.
    """
    formatter = JSONFormatter()
    
    # 1. Standard log formatting
    log_record = logging.LogRecord(
        name="replayiq",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Task completed successfully",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(log_record)
    import json
    parsed = json.loads(formatted)
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "replayiq"
    assert parsed["message"] == "Task completed successfully"
    assert "timestamp" in parsed

    # 2. Uvicorn access log formatting
    access_record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="uvicorn",
        lineno=50,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:51234", "GET", "/api/v1/health", "HTTP/1.1", 200),
        exc_info=None
    )
    formatted_access = formatter.format(access_record)
    parsed_access = json.loads(formatted_access)
    assert parsed_access["logger"] == "uvicorn.access"
    assert parsed_access["client_ip"] == "127.0.0.1:51234"
    assert parsed_access["method"] == "GET"
    assert parsed_access["path"] == "/api/v1/health"
    assert parsed_access["status_code"] == 200

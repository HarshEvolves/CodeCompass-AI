import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import status
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.api_log import ApiLog

def test_create_log_successful(client, db_session):
    """
    Verifies that a user can successfully create an API log under a project they own.
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
        "url": "http://api.example.com/data",
        "request_headers": {"Content-Type": "application/json"},
        "request_body": {"info": "some request payload"},
        "response_headers": {"Server": "nginx"},
        "response_body": {"success": True},
        "status_code": 201,
        "response_time_ms": 120
    }

    response = client.post(f"/projects/{project.id}/logs", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["url"] == "http://api.example.com/data"
    assert data["method"] == "POST"
    assert data["status_code"] == 201
    assert data["response_time_ms"] == 120
    assert data["project_id"] == str(project.id)
    assert "id" in data

def test_create_log_validations(client, db_session):
    """
    Verifies input constraints for API logs (valid HTTP methods, status code range, positive latency, non-empty URL).
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

    # 1. Invalid HTTP method (PATCH is allowed, but e.g. "OPTIONS" is not in Literal["GET", "POST", "PUT", "DELETE", "PATCH"])
    payload = {
        "method": "OPTIONS",
        "url": "http://api.example.com",
        "status_code": 200,
        "response_time_ms": 50
    }
    response = client.post(f"/projects/{project.id}/logs", json=payload, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. Out of range status_code (99 or 600)
    payload = {
        "method": "GET",
        "url": "http://api.example.com",
        "status_code": 99,
        "response_time_ms": 50
    }
    response = client.post(f"/projects/{project.id}/logs", json=payload, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 3. Negative response time
    payload = {
        "method": "GET",
        "url": "http://api.example.com",
        "status_code": 200,
        "response_time_ms": -5
    }
    response = client.post(f"/projects/{project.id}/logs", json=payload, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 4. Empty URL
    payload = {
        "method": "GET",
        "url": "",
        "status_code": 200,
        "response_time_ms": 50
    }
    response = client.post(f"/projects/{project.id}/logs", json=payload, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_logs_filters_and_pagination(client, db_session):
    """
    Verifies retrieving manual project logs, sorting newest first, filters by method and status, and pagination.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Test Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    # Create logs with distinct created_at times (oldest to newest: log1, log2, log3)
    now = datetime.now(timezone.utc)
    log1 = ApiLog(
        project_id=project.id,
        method="GET",
        url="http://api.example.com/1",
        status_code=200,
        response_time_ms=10,
        created_at=now - timedelta(minutes=10)
    )
    log2 = ApiLog(
        project_id=project.id,
        method="POST",
        url="http://api.example.com/2",
        status_code=201,
        response_time_ms=20,
        created_at=now - timedelta(minutes=5)
    )
    log3 = ApiLog(
        project_id=project.id,
        method="GET",
        url="http://api.example.com/3",
        status_code=400,
        response_time_ms=30,
        created_at=now
    )
    db_session.add_all([log1, log2, log3])
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch all newest first
    response = client.get(f"/projects/{project.id}/logs", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    assert data[0]["url"] == "http://api.example.com/3"
    assert data[1]["url"] == "http://api.example.com/2"
    assert data[2]["url"] == "http://api.example.com/1"

    # 2. Pagination: page=2, limit=1
    response = client.get(f"/projects/{project.id}/logs?page=2&limit=1", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    paginated_data = response.json()
    assert len(paginated_data) == 1
    assert paginated_data[0]["url"] == "http://api.example.com/2"

    # 3. Filter by method
    response = client.get(f"/projects/{project.id}/logs?method=POST", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    assert results[0]["method"] == "POST"

    # 4. Filter by status_code
    response = client.get(f"/projects/{project.id}/logs?status_code=200", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    assert results[0]["status_code"] == 200

def test_user_cannot_access_another_user_logs(client, db_session):
    """
    Verifies that querying, listing, or deleting logs under a project owned by another user yields 404.
    """
    hashed_pass = get_password_hash("password123")
    user1 = User(full_name="User One", email="user1@example.com", hashed_password=hashed_pass)
    user2 = User(full_name="User Two", email="user2@example.com", hashed_password=hashed_pass)
    db_session.add_all([user1, user2])
    db_session.commit()

    project = Project(name="Project User 1", owner_id=user1.id)
    db_session.add(project)
    db_session.commit()

    log = ApiLog(
        project_id=project.id,
        method="GET",
        url="http://api.example.com",
        status_code=200,
        response_time_ms=10
    )
    db_session.add(log)
    db_session.commit()

    # Authenticate as User 2 (not the owner of the project)
    token = create_access_token(data={"sub": user2.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Create log -> 404
    response = client.post(f"/projects/{project.id}/logs", json={"method": "GET", "url": "http://test", "status_code": 200, "response_time_ms": 10}, headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # List logs -> 404
    response = client.get(f"/projects/{project.id}/logs", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Get single log -> 404
    response = client.get(f"/projects/{project.id}/logs/{log.id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Delete log -> 404
    response = client.delete(f"/projects/{project.id}/logs/{log.id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_log_successful(client, db_session):
    """
    Verifies that a user can delete a manual log under their owned project.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Test Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    log = ApiLog(
        project_id=project.id,
        method="GET",
        url="http://api.example.com",
        status_code=200,
        response_time_ms=10
    )
    db_session.add(log)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Delete log
    response = client.delete(f"/projects/{project.id}/logs/{log.id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify database record deleted
    assert db_session.query(ApiLog).filter(ApiLog.id == log.id).count() == 0

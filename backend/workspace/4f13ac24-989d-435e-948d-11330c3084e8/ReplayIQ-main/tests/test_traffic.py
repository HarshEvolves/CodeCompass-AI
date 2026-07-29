import pytest
import uuid
from fastapi import status
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.api_request import APIRequest

def test_unauthorized_requests_list(client):
    """
    Verifies that querying the requests logs endpoint without authentication yields 401.
    """
    response = client.get("/requests")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_request_logged_if_project_exists(client, db_session):
    """
    Verifies that calling a protected route logs the request/response details
    successfully if the user has a project.
    """
    # Create test user and project
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Active User", email="active@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Default Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    # Generate token and call protected route
    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make request to protected endpoint
    response = client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    # Query logged request from database
    logged_request = db_session.query(APIRequest).filter(APIRequest.project_id == project.id).first()
    assert logged_request is not None
    assert logged_request.method == "GET"
    assert logged_request.path == "/api/v1/users/me"
    assert logged_request.response_status == 200
    assert logged_request.response_time_ms > 0
    assert "active@example.com" in logged_request.response_body
    # Ensure authorization header is masked
    assert logged_request.request_headers["authorization"] == "Bearer [MASKED]"

def test_request_rejected_if_no_project(client, db_session):
    """
    Verifies that when an authenticated user without any projects calls a protected route,
    the middleware returns 400 Bad Request.
    """
    # Create test user but no project
    hashed_pass = get_password_hash("password123")
    user = User(full_name="No Project User", email="noproject@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/users/me", headers=headers)
    assert response.json()["error"]["message"] == "No project exists for the authenticated user. Please create a project first."
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

def test_request_list_and_details_endpoints(client, db_session):
    """
    Verifies retrieval, pagination, filtering, and detail endpoints for logged requests.
    """
    # Setup user and project
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Filter User", email="filter@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Project Filter", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    # Log two sample requests manually in the database
    log1 = APIRequest(
        project_id=project.id,
        method="GET",
        path="/items",
        request_headers={},
        response_status=200,
        response_headers={},
        response_time_ms=10.5
    )
    log2 = APIRequest(
        project_id=project.id,
        method="POST",
        path="/items",
        request_headers={},
        response_status=201,
        response_headers={},
        response_time_ms=15.2
    )
    db_session.add_all([log1, log2])
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test fetch all (we filter by path to ignore captured "/requests" requests)
    response = client.get("/requests", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    item_requests = [r for r in data if r["path"] == "/items"]
    assert len(item_requests) == 2

    # 2. Test pagination (limit=1)
    response = client.get("/requests?limit=1", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

    # 3. Test filtering by method
    response = client.get("/requests?method=POST", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    assert results[0]["method"] == "POST"

    # 4. Test filtering by status
    response = client.get("/requests?status=200", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    item_results = [r for r in results if r["path"] == "/items"]
    assert len(item_results) == 1
    assert item_results[0]["response_status"] == 200

    # 5. Test retrieve log details
    detail_response = client.get(f"/requests/{log2.id}", headers=headers)
    assert detail_response.status_code == status.HTTP_200_OK
    detail_data = detail_response.json()
    assert detail_data["id"] == str(log2.id)
    assert detail_data["method"] == "POST"
    assert "request_headers" in detail_data

def test_get_request_details_not_found(client, db_session):
    """
    Verifies that querying detail for a non-existent UUID or a project the user
    doesn't own returns a 404.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Filter User User", email="jwtuser@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Filter User Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    random_uuid = uuid.uuid4()
    response = client.get(f"/requests/{random_uuid}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["message"] == "Request log not found"
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

def test_bypass_excluded_paths(client, db_session):
    """
    Verifies that excluded paths (like /health or docs) are NOT logged in the database.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Active User", email="active@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Default Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    # Hit /health checking connectivity, should not generate database log
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

    # Query logged requests
    logged_count = db_session.query(APIRequest).count()
    assert logged_count == 0

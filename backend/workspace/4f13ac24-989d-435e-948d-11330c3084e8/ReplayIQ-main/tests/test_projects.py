import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import status
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.project import Project

def test_create_project_successful(client, db_session):
    """
    Verifies that an authenticated user can create a project successfully.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="User Creator", email="creator@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/projects",
        json={"name": "Project Alpha", "description": "Alpha Description"},
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Project Alpha"
    assert data["description"] == "Alpha Description"
    assert data["owner_id"] == str(user.id)
    assert "id" in data

def test_create_project_validation_error(client, db_session):
    """
    Verifies that validation constraints (empty name or too long) return 422.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="User Validation", email="validation@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Name is empty
    response = client.post("/projects", json={"name": ""}, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Name is too long (exceeds 100 characters)
    long_name = "a" * 101
    response = client.post("/projects", json={"name": long_name}, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_projects_list_and_pagination(client, db_session):
    """
    Verifies paginated retrieval of user's projects, sorted newest first.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="List User", email="list@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    # Set distinct created_at times (newest to oldest: Project Three, Project Two, Project One)
    now = datetime.now(timezone.utc)
    p1 = Project(name="Project One", owner_id=user.id, created_at=now - timedelta(minutes=10))
    p2 = Project(name="Project Two", owner_id=user.id, created_at=now - timedelta(minutes=5))
    p3 = Project(name="Project Three", owner_id=user.id, created_at=now)
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch all with default limit=10
    response = client.get("/projects", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    # Check that sorting is newest first
    assert data[0]["name"] == "Project Three"
    assert data[1]["name"] == "Project Two"
    assert data[2]["name"] == "Project One"

    # Test pagination: page=2, limit=1
    response = client.get("/projects?page=2&limit=1", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    paginated_data = response.json()
    assert len(paginated_data) == 1
    assert paginated_data[0]["name"] == "Project Two"

def test_get_single_project_successful(client, db_session):
    """
    Verifies that an authenticated owner can query a single project details.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Target Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/projects/{project.id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Target Project"

def test_user_cannot_access_another_user_project(client, db_session):
    """
    Verifies that querying, updating, or deleting another user's project yields 404.
    """
    hashed_pass = get_password_hash("password123")
    user1 = User(full_name="User One", email="user1@example.com", hashed_password=hashed_pass)
    user2 = User(full_name="User Two", email="user2@example.com", hashed_password=hashed_pass)
    db_session.add_all([user1, user2])
    db_session.commit()

    # User 1 owns the project
    project = Project(name="Secret Project", owner_id=user1.id)
    db_session.add(project)
    db_session.commit()

    # Authenticate as User 2
    token = create_access_token(data={"sub": user2.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Query details (GET) -> 404
    response = client.get(f"/projects/{project.id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Update project (PUT) -> 404
    response = client.put(f"/projects/{project.id}", json={"name": "Hacked Name"}, headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Delete project (DELETE) -> 404
    response = client.delete(f"/projects/{project.id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_project_successful(client, db_session):
    """
    Verifies that an owner can update project parameters.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Original Name", description="Original Desc", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        f"/projects/{project.id}",
        json={"name": "Updated Name", "description": "Updated Desc"},
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated Desc"

def test_delete_project_successful(client, db_session):
    """
    Verifies that an owner can delete a project record.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Delete Target", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/projects/{project.id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it is deleted
    assert db_session.query(Project).filter(Project.id == project.id).count() == 0

def test_get_project_invalid_id(client, db_session):
    """
    Verifies that querying details with a non-existent UUID yields 404,
    and a malformed UUID yields 422.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Owner User", email="owner@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Non-existent UUID -> 404
    non_existent_uuid = uuid.uuid4()
    response = client.get(f"/projects/{non_existent_uuid}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Malformed UUID -> 422
    response = client.get("/projects/invalid-uuid-string", headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

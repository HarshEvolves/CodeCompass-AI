import pytest
from datetime import timedelta
from fastapi import status
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.project import Project


def test_successful_registration(client):
    """
    Verifies that a user can register successfully with valid credentials,
    email, password, and full name.
    """
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword", "full_name": "New User"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["full_name"] == "New User"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data  # Ensure plain-text password is not returned

def test_duplicate_email_registration(client, db_session):
    """
    Verifies that registering a duplicate email returns a 400 Bad Request.
    """
    # Pre-populate user in database
    hashed_pass = get_password_hash("password123")
    user = User(full_name="User One", email="duplicate@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "securepassword", "full_name": "User Two"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["message"] == "Email already registered"
    assert response.json()["error"]["code"] == "DUPLICATE_RESOURCE"

def test_successful_login(client, db_session):
    """
    Verifies that correct credentials yield a JWT access token.
    """
    # Pre-populate user in database
    hashed_pass = get_password_hash("correctpassword")
    user = User(full_name="Login User", email="login@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "correctpassword"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_invalid_password_login(client, db_session):
    """
    Verifies that logging in with an invalid password returns a 401 Unauthorized.
    """
    hashed_pass = get_password_hash("correctpassword")
    user = User(full_name="Login User", email="login@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["message"] == "Invalid email or password"
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_access_protected_endpoint_valid_jwt(client, db_session):
    """
    Verifies that a user can query the profile endpoint with a valid access token.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="JWT User", email="jwtuser@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="JWT User Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    # Create active JWT
    token = create_access_token(data={"sub": user.email})

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "jwtuser@example.com"
    assert data["full_name"] == "JWT User"

def test_access_protected_endpoint_missing_jwt(client):
    """
    Verifies that querying a protected route without Authorization headers returns a 401.
    """
    response = client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["message"] == "Not authenticated"
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

def test_access_protected_endpoint_invalid_jwt(client):
    """
    Verifies that querying a protected route with an invalid token returns a 401.
    """
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalidtokenvalue123"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["message"] == "Could not validate credentials"
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

def test_access_protected_endpoint_expired_jwt(client, db_session):
    """
    Verifies that an expired JWT token returns a 401 Unauthorized with "Token has expired" detail.
    """
    hashed_pass = get_password_hash("password123")
    user = User(full_name="Expired User", email="expired@example.com", hashed_password=hashed_pass)
    db_session.add(user)
    db_session.commit()

    project = Project(name="Expired User Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    # Generate a token that expired 10 minutes ago
    expired_delta = timedelta(minutes=-10)
    token = create_access_token(data={"sub": user.email}, expires_delta=expired_delta)


    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["message"] == "Token has expired"
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"

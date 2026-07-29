from sqlalchemy.orm import Session
from app.models.user import User
from app.models.project import Project

def test_create_user(db_session: Session):
    """
    Verifies that a User instance can be created successfully in the database
    with correctly initialized columns and default values.
    """
    user = User(
        full_name="Harsh",
        email="testuser@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()

    # Retrieve and verify properties
    queried_user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    assert queried_user is not None
    assert queried_user.full_name == "Harsh"
    assert queried_user.email == "testuser@example.com"
    assert queried_user.hashed_password == "hashedpassword123"
    assert queried_user.id is not None
    assert queried_user.created_at is not None
    assert queried_user.updated_at is not None

def test_create_project(db_session: Session):
    """
    Verifies that a Project instance can be created and successfully linked
    to an existing User record via owner_id foreign key.
    """
    user = User(
        full_name="Owner One",
        email="owner1@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()

    project = Project(
        name="Project A",
        description="Test project description",
        owner_id=user.id
    )
    db_session.add(project)
    db_session.commit()

    # Retrieve and verify properties and relationship references
    queried_project = db_session.query(Project).filter(Project.name == "Project A").first()
    assert queried_project is not None
    assert queried_project.name == "Project A"
    assert queried_project.description == "Test project description"
    assert queried_project.owner_id == user.id
    assert queried_project.owner.full_name == "Owner One"

def test_user_owns_multiple_projects(db_session: Session):
    """
    Verifies that a single User can own multiple Projects and the ORM
    relationship resolves the list of children correctly.
    """
    user = User(
        full_name="Multi Owner",
        email="multiowner@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()

    p1 = Project(name="Project 1", owner_id=user.id)
    p2 = Project(name="Project 2", owner_id=user.id)
    db_session.add_all([p1, p2])
    db_session.commit()

    db_session.refresh(user)
    assert len(user.projects) == 2
    names = [p.name for p in user.projects]
    assert "Project 1" in names
    assert "Project 2" in names

def test_user_delete_cascades_to_projects(db_session: Session):
    """
    Verifies that when a User is deleted, all their associated projects
    are automatically deleted from the database via cascade constraints.
    """
    user = User(
        full_name="Cascade Target",
        email="cascadetarget@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()

    p = Project(name="Cascaded Project", owner_id=user.id)
    db_session.add(p)
    db_session.commit()

    # Confirm it exists first
    assert db_session.query(Project).filter(Project.name == "Cascaded Project").count() == 1

    # Delete User
    db_session.delete(user)
    db_session.commit()

    # Confirm Project is deleted automatically
    assert db_session.query(Project).filter(Project.name == "Cascaded Project").count() == 0

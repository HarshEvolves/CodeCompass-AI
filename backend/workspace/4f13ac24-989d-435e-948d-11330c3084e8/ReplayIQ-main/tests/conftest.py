import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

@pytest.fixture(scope="session")
def db_engine():
    """
    Session-wide fixture that initializes the database engine.
    """
    engine = create_engine(settings.sql_database_url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Function-scoped fixture that provides a database session.
    Wraps all operations in a transaction and rolls it back at the end of the test,
    ensuring tests do not pollute the database.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    
    # Session local bound to the active transactional connection
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection
    )
    session = TestingSessionLocal()
    
    # Clean the database before running each test function to guarantee isolation
    from app.models.api_request import APIRequest
    from app.models.replay import Replay
    from app.models.api_log import ApiLog
    from app.models.project import Project
    from app.models.user import User

    session.query(APIRequest).delete()
    session.query(Replay).delete()
    session.query(ApiLog).delete()
    session.query(Project).delete()
    session.query(User).delete()
    session.commit()
    
    yield session
    
    # Rollback transactions and close connections to isolate tests
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """
    Function-scoped fixture that provides a TestClient with the get_db dependency
    overridden to use our transactional db_session fixture.
    Automatically prepends the API_V1_STR prefix to requests targeting v1 endpoints.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.dependencies.db import get_db

    class ApiV1TestClient(TestClient):
        def request(self, method, url, *args, **kwargs):
            # Prepend API version prefix if path starts with '/' and is not health/docs/redoc/root
            if url.startswith("/") and not (
                url.startswith("/health")
                or url == "/"
                or url.startswith("/docs")
                or url.startswith("/redoc")
                or url.startswith("/openapi.json")
            ):
                url = f"{settings.API_V1_STR}{url}"
            return super().request(method, url, *args, **kwargs)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override get_db in dependency_overrides
    app.dependency_overrides[get_db] = override_get_db
    
    # Expose the active transactional session to middleware during testing
    app.state.db_session = db_session
    
    with ApiV1TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
        
    # Clear overrides and app state references after the test completes
    app.dependency_overrides.clear()
    if hasattr(app.state, "db_session"):
        delattr(app.state, "db_session")


@pytest.fixture
def anyio_backend():
    """
    Restricts anyio tests to the asyncio backend, bypassing the missing trio dependency.
    """
    return "asyncio"



from typing import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    """
    FastAPI dependency that yields a database session.
    The session is automatically created and then closed after the request is processed,
    ensuring proper connection clean-up and preventing leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

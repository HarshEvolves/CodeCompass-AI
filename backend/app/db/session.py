"""
CodeCompass Database Session Management

This module sets up async PostgreSQL connection handling using SQLAlchemy.
It exports:
  - engine: The connection manager.
  - AsyncSessionLocal: The factory creating individual database sessions.
  - Base: The declarative base class for future SQLAlchemy models.
  - get_db: An asynchronous generator function to fetch database sessions.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ─── Async Database Engine ──────────────────────────────────────────
# The async engine controls the database connection pool.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # Logs raw SQL queries to console when DEBUG=True
    pool_pre_ping=True,        # Checks connection health prior to routing queries
)

# ─── Async Session Factory ──────────────────────────────────────────
# Generates scoped transactional operations asynchronously.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Keeps properties readable after transaction commit
)


# ─── Declarative Base Model ─────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Common base class for all database models.
    All future ORM models (e.g. User, Project) must inherit from this class.
    """
    pass


# ─── Dependency: Scoped Async Database Session ──────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding a single database session per request.
    Handles commit operations automatically, rolling back in case of exceptions,
    and guarantees proper closure of connection resources.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

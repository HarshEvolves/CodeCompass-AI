"""
CodeCompass Database Session Management
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# ─── Create Async Database Engine ──────────────────────────────────
# Manages connections asynchronously
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True
)

# ─── Create Async Session Factory ──────────────────────────────────
# Generates active transactional sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ─── Declarative Base Model ────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Subclass DeclarativeBase to trace model attributes for future migrations.
    """
    pass


# ─── Dependency: Scoped Session Generator ──────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a transactional database session context per query lifespan.
    Automatically commits, rolls back on exceptions, and closes connections.
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

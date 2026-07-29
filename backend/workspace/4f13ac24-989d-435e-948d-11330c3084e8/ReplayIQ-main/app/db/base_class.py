from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 style declarative base class.
    All database models will inherit from this Base class.
    This centralized base class allows Alembic to detect model schemas for migrations.
    """
    pass

class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timezone-aware datetime fields
    to any SQLAlchemy model inheriting from it.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


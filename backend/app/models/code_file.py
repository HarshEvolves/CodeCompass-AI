"""
CodeCompass CodeFile DB Model
"""
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CodeFile(Base):
    """
    SQLAlchemy model representing a parsed source code file within an uploaded repository.
    """
    __tablename__ = "code_files"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    relative_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False
    )
    language: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    total_lines: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

"""
CodeCompass CodeChunk DB Model
"""
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CodeChunk(Base):
    """
    SQLAlchemy model representing a text/code chunk of a parsed source file.
    """
    __tablename__ = "code_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    code_file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("code_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

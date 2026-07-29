import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, UUID, Integer, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class ApiLog(Base):
    """
    SQLAlchemy model representing a manually stored API request/response transaction log.
    """
    __tablename__ = "api_logs"

    # UUID primary key using native postgresql UUID column type
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Associated Project foreign key reference
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request metrics
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    
    request_headers: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    request_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Response metrics
    response_headers: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    # Many ApiLogs belong to one Project
    project: Mapped["Project"] = relationship("Project", back_populates="api_logs")
    # One ApiLog can have many execution Replays
    replays: Mapped[list["Replay"]] = relationship("Replay", back_populates="api_log", cascade="all, delete-orphan")


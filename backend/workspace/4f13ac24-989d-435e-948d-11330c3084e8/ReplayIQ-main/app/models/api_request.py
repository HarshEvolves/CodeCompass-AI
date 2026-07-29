import uuid
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, UUID, Integer, Float, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class APIRequest(Base):
    """
    SQLAlchemy model representing an intercepted API Request/Response transaction.
    """
    __tablename__ = "api_requests"

    # UUID primary key using native UUID column type
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Associated Project foreign key
    # ondelete="CASCADE" deletes logged traffic requests when projects are removed
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Request metadata
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    query_params: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    request_headers: Mapped[dict] = mapped_column(JSON, nullable=False)
    request_body: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Response metadata
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_headers: Mapped[dict] = mapped_column(JSON, nullable=False)
    response_body: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Performance metric (latency)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Client identifier
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    
    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    # Many APIRequests belong to one Project
    project: Mapped["Project"] = relationship("Project")

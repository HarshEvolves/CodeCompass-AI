import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, UUID, Integer, DateTime, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Replay(Base):
    """
    SQLAlchemy model representing the results of a manual request replay attempt.
    """
    __tablename__ = "replays"

    # UUID primary key using native postgresql UUID column type
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Associated ApiLog foreign key reference
    api_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Replay metrics and values (nullable to accommodate connection/dns/timeout failures)
    replay_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replay_response_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    replay_response_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    replay_response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Status metrics
    replay_success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    
    # Timestamp of execution
    replayed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    # Many Replays belong to one ApiLog
    api_log: Mapped["ApiLog"] = relationship("ApiLog", back_populates="replays")

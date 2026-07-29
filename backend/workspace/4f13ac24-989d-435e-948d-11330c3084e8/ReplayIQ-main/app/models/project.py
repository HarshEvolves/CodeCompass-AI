import uuid
from sqlalchemy import ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, TimestampMixin

class Project(Base, TimestampMixin):
    """
    SQLAlchemy model representing a Project in ReplayIQ.
    Each Project belongs to exactly one owner (User).
    """
    __tablename__ = "projects"

    # UUID primary key using native postgresql UUID column type
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    # Project name (indexed for name-based searches)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    # Project description (nullable)
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    # Foreign key referencing User.id (indexed for fast query joins)
    # ondelete="CASCADE" ensures project references are cleaned up when users are deleted.
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    # Bidirectional relationship with the User model.
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
    )
    # One Project can have many manually captured API logs
    api_logs: Mapped[list["ApiLog"]] = relationship(
        "ApiLog",
        back_populates="project",
        cascade="all, delete-orphan"
    )


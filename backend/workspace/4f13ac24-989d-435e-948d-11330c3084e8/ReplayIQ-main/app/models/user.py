import uuid
from typing import List
from sqlalchemy import String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, TimestampMixin

class User(Base, TimestampMixin):
    """
    SQLAlchemy model representing a User in the ReplayIQ system.
    Inherits from the declarative Base and the TimestampMixin.
    """
    __tablename__ = "users"

    # UUID primary key using native postgresql UUID column type
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    # Full name of the user
    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Unique, indexed email address
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    # Store hashed password
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Relationships
    # Bidirectional relationship with the Project model.
    # cascade="all, delete-orphan" removes projects owned by this user upon deletion.
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

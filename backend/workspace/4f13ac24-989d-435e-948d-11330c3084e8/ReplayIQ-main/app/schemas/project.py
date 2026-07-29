import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

class ProjectBase(BaseModel):
    """
    Base validation class for Project fields.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The display name of the project. Cannot be empty or exceed 100 characters."
    )
    description: str | None = Field(
        None,
        max_length=1000,
        description="Optional description detailing the project's purpose."
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Strip whitespace and reject blank names."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Project name cannot be blank")
        return stripped

class ProjectCreate(ProjectBase):
    """
    Validation schema for creating a project.
    """
    pass

class ProjectUpdate(BaseModel):
    """
    Validation schema for updating a project.
    All attributes are optional to support partial updates (PATCH style in PUT).
    """
    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Optional updated name of the project."
    )
    description: str | None = Field(
        None,
        max_length=1000,
        description="Optional updated description of the project."
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        """Strip whitespace and reject blank names when provided."""
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Project name cannot be blank")
            return stripped
        return v

class ProjectResponse(BaseModel):
    """
    Validation schema for output project representation.
    """
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Enable reading directly from SQLAlchemy database models
    model_config = ConfigDict(from_attributes=True)

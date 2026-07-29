import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

class UserBase(BaseModel):
    """
    Base attributes for User schemas.
    """
    full_name: str = Field(..., min_length=1, max_length=100, description="User's display name")
    email: EmailStr

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_blank(cls, v: str) -> str:
        """Strip whitespace and reject blank display names."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Full name cannot be blank")
        return stripped

class UserCreate(UserBase):
    """
    Schema for user registration request input.
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters long",
    )

class UserResponse(BaseModel):
    """
    Schema validating the serialized response payload of User data.
    """
    id: uuid.UUID
    full_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime


    # Enable pydantic from_attributes to support reading attributes directly from ORM models
    model_config = ConfigDict(from_attributes=True)

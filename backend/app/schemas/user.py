"""
CodeCompass User Validation Schemas
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Shared fields between registration and response schemas.
    """
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """
    Validation schema for creating a new user registration.
    """
    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """
    Response schema returning non-sensitive user metadata to the client.
    """
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Enable Pydantic to read ORM objects directly
    model_config = {
        "from_attributes": True
    }

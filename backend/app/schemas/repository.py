"""
CodeCompass Repository Schema Validations
"""
import uuid
from datetime import datetime
from pydantic import BaseModel


class RepositoryBase(BaseModel):
    """
    Shared repository metadata fields.
    """
    name: str


class RepositoryResponse(RepositoryBase):
    """
    Response schema representing saved repository metadata records.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    storage_path: str
    upload_status: str
    created_at: datetime
    updated_at: datetime

    # Parse ORM instances directly
    model_config = {
        "from_attributes": True
    }

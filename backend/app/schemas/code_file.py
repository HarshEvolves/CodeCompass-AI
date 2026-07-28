"""
CodeCompass CodeFile Schema Validations
"""
import uuid
from datetime import datetime
from pydantic import BaseModel


class CodeFileResponse(BaseModel):
    """
    Response schema representing the metadata of a parsed code file.
    """
    id: uuid.UUID
    repository_id: uuid.UUID
    relative_path: str
    language: str
    file_size: int
    total_lines: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

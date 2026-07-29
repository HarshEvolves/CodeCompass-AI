import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

class ApiLogBase(BaseModel):
    """
    Base validation schema for manual API Log attributes.
    """
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(
        ...,
        description="Must be a standard HTTP verb: GET, POST, PUT, DELETE, or PATCH."
    )
    url: str = Field(
        ...,
        min_length=1,
        description="The URL endpoint of the logged request. Cannot be empty."
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is absolute or starts with a slash."""
        v = v.strip()
        if not v.startswith("http://") and not v.startswith("https://") and not v.startswith("/"):
            raise ValueError("URL must be a relative path starting with '/' or an absolute URL starting with 'http://' or 'https://'")
        return v
    request_headers: dict = Field(
        default_factory=dict,
        description="Request headers dictionary."
    )
    request_body: dict | None = Field(
        None,
        description="Optional request body payload JSON dictionary."
    )
    response_headers: dict = Field(
        default_factory=dict,
        description="Response headers dictionary."
    )
    response_body: dict | None = Field(
        None,
        description="Optional response body payload JSON dictionary."
    )
    status_code: int = Field(
        ...,
        ge=100,
        le=599,
        description="Response HTTP status code. Must be between 100 and 599."
    )
    response_time_ms: int = Field(
        ...,
        ge=0,
        description="Transaction response latency in milliseconds. Cannot be negative."
    )

class ApiLogCreate(ApiLogBase):
    """
    Input schema for storing a new manual API Request log.
    """
    pass

class ApiLogResponse(ApiLogBase):
    """
    Output serialization schema for API Request logs details.
    """
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime

    # Map attributes from database ORM models automatically
    model_config = ConfigDict(from_attributes=True)

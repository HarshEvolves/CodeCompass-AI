import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class APIRequestResponse(BaseModel):
    """
    Pydantic schema representing simplified information of captured API requests.
    Used for listing request logs in API logs history.
    """
    id: uuid.UUID
    project_id: uuid.UUID
    method: str
    path: str
    response_status: int
    response_time_ms: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class APIRequestDetailResponse(APIRequestResponse):
    """
    Pydantic schema representing the full detailed payload parameters of
    an intercepted API request transaction.
    """
    query_params: str | None
    request_headers: dict
    request_body: str | None
    response_headers: dict
    response_body: str | None
    client_ip: str | None

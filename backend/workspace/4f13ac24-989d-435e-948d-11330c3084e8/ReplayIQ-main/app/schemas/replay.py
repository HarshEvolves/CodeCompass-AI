import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ReplayResponse(BaseModel):
    """
    Pydantic schema representing the serialized response output of an execution Replay.
    """
    id: uuid.UUID
    api_log_id: uuid.UUID
    replay_status_code: int | None
    replay_response_headers: dict | None
    replay_response_body: dict | None
    replay_response_time_ms: int | None
    replay_success: bool
    error_message: str | None
    replayed_at: datetime

    # Enable reading directly from SQLAlchemy database models
    model_config = ConfigDict(from_attributes=True)

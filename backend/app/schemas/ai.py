from pydantic import BaseModel, Field

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="The message to send to the AI")

class AIChatResponse(BaseModel):
    success: bool
    response: str

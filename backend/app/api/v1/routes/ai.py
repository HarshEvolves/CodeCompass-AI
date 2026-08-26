import logging
from fastapi import APIRouter, HTTPException
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.llm_service import chat_with_gemini

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)

@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(request: AIChatRequest):
    """
    Generic AI chat endpoint.
    Sends a message to the configured AI model and returns the response.
    """
    logger.info("Request received at /ai/chat")
    try:
        response_text = await chat_with_gemini(request.message)
        return AIChatResponse(success=True, response=response_text)
    except HTTPException:
        # Re-raise HTTP exceptions from the service layer
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /ai/chat: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

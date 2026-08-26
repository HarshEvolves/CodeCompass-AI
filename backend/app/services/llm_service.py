import logging
import time
import httpx
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

async def chat_with_gemini(message: str) -> str:
    """
    Sends a message to the Gemini API and returns the response.
    """
    gemini_key = getattr(settings, "GEMINI_API_KEY", None)
    if not gemini_key:
        logger.error("GEMINI_API_KEY is not configured.")
        raise HTTPException(status_code=500, detail="AI service is not configured.")

    model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
    
    payload = {
        "contents": [{"parts": [{"text": message}]}]
    }
    
    logger.info("Gemini request started.")
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=30.0)
            elapsed = time.time() - start_time
            
            if res.status_code != 200:
                logger.error(f"Gemini API error ({res.status_code}): {res.text} (Time: {elapsed:.2f}s)")
                raise HTTPException(status_code=502, detail="Error communicating with AI service.")
            
            res_data = res.json()
            answer = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            logger.info(f"Gemini response received successfully in {elapsed:.2f}s.")
            return answer
            
        except httpx.TimeoutException:
            elapsed = time.time() - start_time
            logger.error(f"Gemini API request timed out after {elapsed:.2f}s.")
            raise HTTPException(status_code=504, detail="AI service request timed out.")
        except httpx.RequestError as exc:
            elapsed = time.time() - start_time
            logger.error(f"Gemini API request failed: {exc} (Time: {elapsed:.2f}s)")
            raise HTTPException(status_code=502, detail="Failed to connect to AI service.")
        except (KeyError, IndexError) as exc:
            elapsed = time.time() - start_time
            logger.error(f"Unexpected response format from Gemini: {exc} (Time: {elapsed:.2f}s)")
            raise HTTPException(status_code=502, detail="Received invalid response from AI service.")

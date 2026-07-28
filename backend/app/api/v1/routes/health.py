from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.core.config import settings
from app.db import get_db

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Minimal health checking endpoint.
    Verifies that the database is reachable.
    """
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected (error: {str(e)})"

    return {
        "status": "healthy" if "disconnected" not in db_status else "degraded",
        "database": db_status,
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }

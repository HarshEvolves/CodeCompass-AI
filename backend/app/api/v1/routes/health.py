"""
Health Check Route

Provides a simple endpoint for monitoring tools, load balancers,
and the frontend to verify the backend is running.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.core.config import settings
from app.db import get_db

# Create a router — this groups related endpoints together.
# It gets registered in main.py with a prefix like /api/v1
router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Returns the current status of the API and its database connection.

    Used by:
      - The frontend landing page (to show "Backend Connected")
      - Docker health checks (in later phases)
      - Monitoring / uptime tools
    """
    db_status = "connected"
    try:
        # Perform a lightweight async database query
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected (error: {str(e)})"

    return {
        "status": "healthy" if "disconnected" not in db_status else "degraded",
        "database": db_status,
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }

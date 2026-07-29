from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies.db import get_db

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify backend service and database status.
    Runs a raw SQL query (SELECT 1) on the database.
    If successful, returns HTTP 200 with status: healthy.
    If database check fails, returns HTTP 503 Service Unavailable.
    """
    try:
        # Executing a simple check to test database connectivity
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )

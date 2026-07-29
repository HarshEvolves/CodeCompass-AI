import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.project_service import ProjectService
from app.services.log_service import LogService
from app.schemas.api_log import ApiLogCreate, ApiLogResponse

router = APIRouter(prefix="/projects/{project_id}/logs", tags=["log-management"])

def get_project_or_404(db: Session, project_id: uuid.UUID, user_id: uuid.UUID):
    """
    Validates project existence and ownership.
    Returns HTTP 404 if project is missing or owned by another user.
    """
    project = ProjectService.get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project

@router.post("", response_model=ApiLogResponse, status_code=status.HTTP_201_CREATED)
def create_log(
    project_id: uuid.UUID,
    log_in: ApiLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stores a new manual API request/response log entry.
    Requires project ownership.
    """
    # Verify that project belongs to the authenticated user
    get_project_or_404(db, project_id, current_user.id)
    
    return LogService.create_log(db, log_in, project_id)

@router.get("", response_model=List[ApiLogResponse])
def get_logs(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items limit per page"),
    method: str | None = Query(None, description="Filter by HTTP method"),
    status_code: int | None = Query(None, alias="status_code", description="Filter by HTTP status code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a paginated list of manual logs for a project owned by the user.
    Supports filtering by method and status code, sorted newest first.
    """
    get_project_or_404(db, project_id, current_user.id)
    
    return LogService.get_logs(
        db=db,
        project_id=project_id,
        page=page,
        limit=limit,
        method=method,
        status_code=status_code
    )

@router.get("/{log_id}", response_model=ApiLogResponse)
def get_log(
    project_id: uuid.UUID,
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves details of a single manual API log.
    Returns HTTP 404 if either the project or the log is not found or not owned.
    """
    get_project_or_404(db, project_id, current_user.id)
    
    log = LogService.get_log_by_id(db, log_id, project_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )
    return log

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(
    project_id: uuid.UUID,
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a manual API log entry.
    Returns HTTP 404 if either the project or the log is not found or not owned.
    """
    get_project_or_404(db, project_id, current_user.id)
    
    log = LogService.get_log_by_id(db, log_id, project_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )
    LogService.delete_log(db, log)

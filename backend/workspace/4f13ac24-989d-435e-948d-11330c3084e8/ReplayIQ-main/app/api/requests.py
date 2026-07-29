import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.api_request import APIRequest
from app.schemas.api_request import APIRequestResponse, APIRequestDetailResponse

router = APIRouter(prefix="/requests", tags=["traffic-capture"])

@router.get("", response_model=List[APIRequestResponse])
def list_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    method: str | None = Query(None, description="Filter by HTTP method (e.g. GET)"),
    status_code: int | None = Query(None, alias="status", description="Filter by response status code"),
    project_id: uuid.UUID | None = Query(None, description="Filter by project UUID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of captured request logs for projects owned by the authenticated user.
    Supports filtering by method, response status code, and specific project ID.
    """
    # Restrict lookup to projects owned by the current authenticated user
    user_project_ids = [p.id for p in current_user.projects]
    if not user_project_ids:
        return []

    query = db.query(APIRequest).filter(APIRequest.project_id.in_(user_project_ids))

    # Apply filters
    if method:
        query = query.filter(APIRequest.method == method.upper())
    if status_code is not None:
        query = query.filter(APIRequest.response_status == status_code)
    if project_id:
        if project_id not in user_project_ids:
            # Avoid leaking traffic from projects the user doesn't own
            return []
        query = query.filter(APIRequest.project_id == project_id)

    # Order by newest first
    query = query.order_by(APIRequest.created_at.desc())
    
    requests = query.offset(skip).limit(limit).all()
    return requests

@router.get("/{request_id}", response_model=APIRequestDetailResponse)
def get_request(
    request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the full detailed headers and body payload of a specific captured request log.
    Ensures that the requested log is owned by the current user's project space.
    """
    user_project_ids = [p.id for p in current_user.projects]
    
    # Query details checking ownership constraints
    request_log = db.query(APIRequest).filter(
        APIRequest.id == request_id,
        APIRequest.project_id.in_(user_project_ids)
    ).first()
    
    if not request_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request log not found"
        )
        
    return request_log

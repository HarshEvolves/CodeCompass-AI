import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.project_service import ProjectService
from app.services.log_service import LogService
from app.services.replay_service import ReplayService
from app.schemas.replay import ReplayResponse

router = APIRouter(prefix="/projects/{project_id}/logs/{log_id}/replay", tags=["replay-engine"])

@router.post("", response_model=ReplayResponse, status_code=status.HTTP_200_OK)
async def replay_log(
    project_id: uuid.UUID,
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers a request replay for a previously saved API log.
    Ensures that:
    - The project exists and belongs to the authenticated user.
    - The API log exists and belongs to the project.
    - The request HTTP method is supported for replay.
    """
    # 1. Verify project exists and belongs to user
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # 2. Verify log exists and belongs to that project
    log = LogService.get_log_by_id(db, log_id, project_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )

    # 3. Reject unsupported HTTP methods (only GET, POST, PUT, PATCH, DELETE are allowed)
    allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    if log.method.upper() not in allowed_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Replay is not supported for HTTP method: {log.method}"
        )

    # 4. Trigger replay via the service layer
    replay_result = await ReplayService.trigger_replay(db, log)
    return replay_result

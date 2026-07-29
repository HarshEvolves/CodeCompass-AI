"""
API router for the Response Comparison Engine (Phase 7).

Exposes:
  GET /projects/{project_id}/logs/{log_id}/replays/{replay_id}/comparison

Authenticates the user, verifies ownership chain (project → log → replay),
then delegates to ComparisonService to produce the comparison JSON.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.replay import Replay
from app.services.project_service import ProjectService
from app.services.log_service import LogService
from app.services.comparison_service import ComparisonService
from app.schemas.comparison import ComparisonResponse

router = APIRouter(
    prefix="/projects/{project_id}/logs/{log_id}/replays/{replay_id}",
    tags=["comparison"],
)


@router.get("/comparison", response_model=ComparisonResponse, status_code=status.HTTP_200_OK)
def get_comparison(
    project_id: uuid.UUID,
    log_id: uuid.UUID,
    replay_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a structured comparison between the original API log
    and a specific replay execution.

    Steps:
      1. Authenticate the user (via JWT dependency).
      2. Verify the project exists and belongs to the authenticated user.
      3. Verify the API log exists and belongs to the project.
      4. Verify the replay exists and belongs to the API log.
      5. Generate and return the comparison JSON.
    """

    # --- 1. Verify project ownership ---
    project = ProjectService.get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # --- 2. Verify log belongs to the project ---
    log = LogService.get_log_by_id(db, log_id, project_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )

    # --- 3. Verify replay belongs to the log ---
    replay = db.query(Replay).filter(
        Replay.id == replay_id,
        Replay.api_log_id == log_id,
    ).first()
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found",
        )

    # --- 4. Generate comparison ---
    comparison = ComparisonService.generate_comparison(log, replay)
    return comparison

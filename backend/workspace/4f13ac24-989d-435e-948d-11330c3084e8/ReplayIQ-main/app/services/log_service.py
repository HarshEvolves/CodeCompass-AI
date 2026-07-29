import uuid
from sqlalchemy.orm import Session
from app.models.api_log import ApiLog
from app.schemas.api_log import ApiLogCreate

class LogService:
    """
    Service layer providing CRUD operations on manually stored ApiLog models.
    """

    @staticmethod
    def create_log(db: Session, log_in: ApiLogCreate, project_id: uuid.UUID) -> ApiLog:
        """
        Creates a new manual API request/response log entry under a project.
        """
        log = ApiLog(
            project_id=project_id,
            method=log_in.method,
            url=log_in.url,
            request_headers=log_in.request_headers,
            request_body=log_in.request_body,
            response_headers=log_in.response_headers,
            response_body=log_in.response_body,
            status_code=log_in.status_code,
            response_time_ms=log_in.response_time_ms
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_logs(
        db: Session,
        project_id: uuid.UUID,
        page: int = 1,
        limit: int = 10,
        method: str | None = None,
        status_code: int | None = None
    ) -> list[ApiLog]:
        """
        Queries all API logs registered under a specific project, paginated and sorted newest first.
        Supports filtering by HTTP method and status code.
        """
        # Calculate offset from page index (1-based index)
        offset = (page - 1) * limit
        
        query = db.query(ApiLog).filter(ApiLog.project_id == project_id)
        
        if method:
            query = query.filter(ApiLog.method == method.upper())
        if status_code is not None:
            query = query.filter(ApiLog.status_code == status_code)
            
        return query.order_by(ApiLog.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_log_by_id(db: Session, log_id: uuid.UUID, project_id: uuid.UUID) -> ApiLog | None:
        """
        Retrieves a single manual log details, verifying project bounds.
        """
        return db.query(ApiLog).filter(
            ApiLog.id == log_id,
            ApiLog.project_id == project_id
        ).first()

    @staticmethod
    def delete_log(db: Session, db_log: ApiLog) -> None:
        """
        Removes a manual API log entry.
        """
        db.delete(db_log)
        db.commit()

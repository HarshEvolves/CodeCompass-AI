import uuid
from sqlalchemy.orm import Session
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    """
    Service layer providing CRUD query interfaces on the Project model.
    Encapsulates transaction management and query construction.
    """
    
    @staticmethod
    def create_project(db: Session, project_in: ProjectCreate, owner_id: uuid.UUID) -> Project:
        """
        Creates a new project record in PostgreSQL, associated with the owner user.
        """
        project = Project(
            name=project_in.name,
            description=project_in.description,
            owner_id=owner_id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_projects(db: Session, owner_id: uuid.UUID, page: int = 1, limit: int = 10) -> list[Project]:
        """
        Queries all projects owned by the specified user, paginated and sorted newest first.
        """
        # Calculate offset from page index (1-based index)
        offset = (page - 1) * limit
        
        return db.query(Project)\
            .filter(Project.owner_id == owner_id)\
            .order_by(Project.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_project_by_id(db: Session, project_id: uuid.UUID, owner_id: uuid.UUID) -> Project | None:
        """
        Retrieves a single project by ID, validating that it belongs to the owner user.
        """
        return db.query(Project)\
            .filter(Project.id == project_id, Project.owner_id == owner_id)\
            .first()

    @staticmethod
    def update_project(db: Session, db_project: Project, project_in: ProjectUpdate) -> Project:
        """
        Updates fields of an existing project.
        """
        if project_in.name is not None:
            db_project.name = project_in.name
        if project_in.description is not None:
            db_project.description = project_in.description

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def delete_project(db: Session, db_project: Project) -> None:
        """
        Deletes a project record from the database.
        """
        db.delete(db_project)
        db.commit()

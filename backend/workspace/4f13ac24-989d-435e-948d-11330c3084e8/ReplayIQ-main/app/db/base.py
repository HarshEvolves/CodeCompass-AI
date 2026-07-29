# Import all the models, so that Base has them before being
# imported by Alembic or the application.
# This prevents circular import errors and helps Alembic discover schemas.

from app.db.base_class import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.api_request import APIRequest  # noqa: F401
from app.models.api_log import ApiLog  # noqa: F401
from app.models.replay import Replay  # noqa: F401





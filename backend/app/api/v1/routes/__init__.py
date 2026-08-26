from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.repositories import router as repositories_router
from app.api.v1.routes.ai import router as ai_router

__all__ = ["health_router", "auth_router", "repositories_router", "ai_router"]




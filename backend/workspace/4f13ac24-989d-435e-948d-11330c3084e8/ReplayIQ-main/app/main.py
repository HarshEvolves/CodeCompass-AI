"""
ReplayIQ — Main Application Entry Point.

Sets up:
  - FastAPI app with rich Swagger documentation
  - Global exception handlers (Phase 9)
  - Structured logging (Phase 9)
  - Traffic capture middleware
  - API v1 router with /api/v1 prefix
  - Un-prefixed utility routes (health, root, redoc)
"""

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exception_handlers import register_exception_handlers
from app.core.responses import ErrorResponse

# ---------------------------------------------------------------------------
# Structured logging — initialise before anything else
# ---------------------------------------------------------------------------
logger = setup_logging(settings.LOG_LEVEL)

# ---------------------------------------------------------------------------
# OpenAPI tag metadata — controls ordering and descriptions in Swagger UI
# ---------------------------------------------------------------------------
tags_metadata = [
    {"name": "health", "description": "Service health checks"},
    {"name": "authentication", "description": "User registration and login"},
    {"name": "users", "description": "Authenticated user profile"},
    {"name": "projects", "description": "Project CRUD operations"},
    {"name": "log-management", "description": "Manual API log management"},
    {"name": "replay-engine", "description": "Replay stored API requests"},
    {"name": "comparison", "description": "Compare original logs with replays"},
    {"name": "analytics", "description": "API log analytics and statistics"},
    {"name": "traffic-capture", "description": "Automatically captured request traffic"},
]

# ---------------------------------------------------------------------------
# FastAPI app initialisation with rich Swagger documentation
# ---------------------------------------------------------------------------
standard_responses = {
    400: {"model": ErrorResponse, "description": "Bad Request / Validation Error"},
    401: {"model": ErrorResponse, "description": "Unauthorized / Authentication Required"},
    403: {"model": ErrorResponse, "description": "Forbidden / Access Denied"},
    404: {"model": ErrorResponse, "description": "Resource Not Found"},
    405: {"model": ErrorResponse, "description": "Method Not Allowed / Not Supported"},
    409: {"model": ErrorResponse, "description": "Conflict / Duplicate Resource"},
    422: {"model": ErrorResponse, "description": "Validation Error"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "**ReplayIQ** — API Replay & Comparison Platform\n\n"
        "ReplayIQ captures, replays, and compares API transactions to detect regressions.\n\n"
        "### Features\n"
        "- 🔐 JWT Authentication\n"
        "- 📁 Project Management\n"
        "- 📝 API Log Storage\n"
        "- 🔄 Request Replay Engine\n"
        "- 🔍 Response Comparison Engine\n"
        "- 📊 Analytics & Statistics\n"
        "- 🚦 Automatic Traffic Capture\n"
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    responses=standard_responses,
    redoc_url=None,
    docs_url="/docs",
    contact={
        "name": "ReplayIQ Team",
    },
    license_info={
        "name": "MIT",
    },
)

# ---------------------------------------------------------------------------
# Global exception handlers (Phase 9)
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.traffic_capture import TrafficCaptureMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrafficCaptureMiddleware)

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ---------------------------------------------------------------------------
# Un-prefixed routes (health, root, redoc)
# ---------------------------------------------------------------------------
from app.api.health import router as health_router
app.include_router(health_router)

# ---------------------------------------------------------------------------
# API v1 router — all feature routes live under /api/v1
# ---------------------------------------------------------------------------
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.requests import router as requests_router
from app.api.projects import router as projects_router
from app.api.logs import router as logs_router
from app.api.replay import router as replay_router
from app.api.comparison import router as comparison_router
from app.api.analytics import router as analytics_router

api_v1_router = APIRouter(prefix=settings.API_V1_STR)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(requests_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(logs_router)
api_v1_router.include_router(replay_router)
api_v1_router.include_router(comparison_router)
api_v1_router.include_router(analytics_router)

app.include_router(api_v1_router)

# ---------------------------------------------------------------------------
# Utility routes (un-prefixed)
# ---------------------------------------------------------------------------

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """
    Custom route to render ReDoc documentation page using the locally served script.
    This is wrapped with a safety script that temporarily clears globally polluted
    variables (like 'module', 'exports', or 'require') injected by browser extensions,
    allowing UMD wrappers to resolve correctly in browser contexts.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>{settings.PROJECT_NAME} - ReDoc</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
    </style>
    </head>
    <body>
    <noscript>
        ReDoc requires Javascript to function. Please enable it to browse the documentation.
    </noscript>
    <redoc spec-url="{app.openapi_url}"></redoc>

    <script>
      // Clean up global pollution from extensions that break UMD wrappers
      var _temp_module = window.module;
      var _temp_exports = window.exports;
      var _temp_require = window.require;
      window.module = undefined;
      window.exports = undefined;
      window.require = undefined;
    </script>

    <script src="/static/redoc.standalone.js"></script>

    <script>
      // Restore globals
      if (_temp_module !== undefined) window.module = _temp_module;
      if (_temp_exports !== undefined) window.exports = _temp_exports;
      if (_temp_require !== undefined) window.require = _temp_require;
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/")
def read_root():
    """
    Optional welcoming root route providing a quick link to the API docs.
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Access /docs for Swagger API documentation.",
        "docs": "/docs",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }

"""
CodeCompass Backend — FastAPI App Core Entry Point
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routes import health_router, auth_router, repositories_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI app lifespan event handler.
    Ensures that dynamic storage and database workspace directories exist on boot.
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI backend starter endpoint configurations.",
    version="1.0.0",
    lifespan=lifespan,
)

# Global unhandled Exception handler to prevent stack trace exposures to clients
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled application exception intercepted:")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please contact system support."},
    )

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(repositories_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """
    Root entrypoint listing documentation URLs.
    """
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "health": "/health"
    }


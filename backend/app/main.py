"""
CodeCompass Backend — FastAPI App Core Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routes import health_router

app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI backend starter endpoint configurations.",
    version="1.0.0"
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


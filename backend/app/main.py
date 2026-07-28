"""
CodeCompass Backend — FastAPI Application Entry Point

This file creates the FastAPI app and wires everything together:
  1. Creates the FastAPI instance
  2. Adds CORS middleware (so the React frontend can call us)
  3. Registers all API routes

Run the server with:
  cd backend
  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import health


# ─── Create FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered codebase explorer — helps developers understand unfamiliar codebases using RAG.",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI: http://localhost:8000/docs
    redoc_url="/redoc",     # ReDoc:      http://localhost:8000/redoc
)


# ─── CORS Middleware ───────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) is a browser security feature.
# Without this, the browser blocks your React app (localhost:5173)
# from calling your FastAPI server (localhost:8000).
#
# This middleware tells the browser: "these origins are allowed."
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Which frontends can access us
    allow_credentials=True,                # Allow cookies / auth headers
    allow_methods=["*"],                   # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],                   # Allow all request headers
)


# ─── Register API Routes ──────────────────────────────────────────
# Each router handles a group of related endpoints.
# The prefix means all routes in health.router start with /api/v1
app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["Health"],
)


# ─── Root Endpoint ────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — returns basic API info."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }

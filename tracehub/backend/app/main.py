"""TraceHub API - Main application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import engine, Base
from .routers import shipments, documents, tracking, webhooks, auth

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create tables if they don't exist (dev only)
    if settings.debug:
        Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title="TraceHub API",
    description="Container tracking and documentation compliance platform for agro-exports",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(shipments.router, prefix="/api/shipments", tags=["Shipments"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Container Tracking"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "TraceHub API",
        "version": "0.1.0",
        "description": "Container tracking and documentation compliance platform",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

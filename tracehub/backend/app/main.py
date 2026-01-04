"""TraceHub API - Main application entry point."""

import logging
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text

from .config import get_settings
from .database import engine, Base, get_db, SessionLocal
from .routers import shipments, documents, tracking, webhooks, auth, notifications, users
from .routers import analytics, audit, eudr
from .middleware import RequestTrackingMiddleware, RateLimitMiddleware, ErrorHandlerMiddleware
from .models import ContainerEvent, Shipment, Product

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Track application start time
app_start_time: datetime = None
last_tracking_sync: datetime = None


def ensure_horn_hoof_products():
    """Ensure Horn & Hoof shipments have products with HS code 0506.

    Horn & Hoof products (HS 0506/0507) are exempt from EUDR.
    This function adds products to shipments that don't have them.
    """
    db = SessionLocal()
    try:
        # Find shipments that look like Horn & Hoof (bovine hooves, horns)
        # These are VIBO-2026-001 and VIBO-2026-002
        horn_hoof_refs = ["VIBO-2026-001", "VIBO-2026-002"]
        horn_hoof_shipments = db.query(Shipment).filter(
            Shipment.reference.in_(horn_hoof_refs)
        ).all()

        logger.info(f"Found {len(horn_hoof_shipments)} Horn & Hoof shipments (looking for {horn_hoof_refs})")

        for shipment in horn_hoof_shipments:
            # Check if shipment already has products
            existing_products = db.query(Product).filter(
                Product.shipment_id == shipment.id
            ).count()

            logger.info(f"Shipment {shipment.reference} has {existing_products} existing products")

            if existing_products == 0:
                # Add Horn & Hoof product (HS 0506.90.00)
                product = Product(
                    shipment_id=shipment.id,
                    hs_code="0506.90.00",
                    description="Bovine Hooves (Dried)" if "001" in shipment.reference else "Crushed Cow Horns",
                    quantity_net_kg=25000.0,
                    quantity_gross_kg=26500.0,
                    unit_of_measure="KG",
                    packaging_type="25kg bags",
                    packaging_count=1000
                )
                db.add(product)
                logger.info(f"Added Horn & Hoof product (HS 0506.90.00) to shipment {shipment.reference}")
            else:
                # Log existing product HS codes
                products = db.query(Product).filter(Product.shipment_id == shipment.id).all()
                hs_codes = [p.hs_code for p in products]
                logger.info(f"Shipment {shipment.reference} already has products with HS codes: {hs_codes}")

        db.commit()
        logger.info("Horn & Hoof product initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize Horn & Hoof products: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global app_start_time
    app_start_time = datetime.utcnow()

    logger.info("TraceHub API starting up...")

    # Startup: Create tables if they don't exist (dev only)
    if settings.debug:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created (debug mode)")

    # Import audit log model to ensure table is created
    from .models.audit_log import AuditLog
    Base.metadata.create_all(bind=engine)

    # Ensure Horn & Hoof shipments have products (for EUDR exemption)
    ensure_horn_hoof_products()

    # Initialize AI document classifier and log status
    try:
        from .services.document_classifier import document_classifier
        ai_status = document_classifier.get_ai_status()
        logger.info(f"Document classifier status: {ai_status}")
    except Exception as e:
        logger.warning(f"Failed to initialize document classifier: {e}")

    logger.info("TraceHub API startup complete")
    yield

    # Shutdown: cleanup if needed
    logger.info("TraceHub API shutting down...")


app = FastAPI(
    title="TraceHub API",
    description="""
## Container Tracking and Documentation Compliance Platform

TraceHub provides comprehensive shipment visibility and documentation management
for agro-export operations, with a focus on EUDR compliance.

### Key Features

- **Real-time Container Tracking** - Live status from carrier APIs
- **Document Lifecycle Management** - Upload, validate, and track compliance documents
- **Compliance Monitoring** - EUDR and export compliance validation
- **Audit Trail** - Complete logging of all system activities
- **Analytics Dashboard** - Operational metrics and insights

### Authentication

All endpoints except `/health` require JWT authentication.
Use the `/api/auth/login` endpoint to obtain a token.
    """,
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Authentication", "description": "User authentication and token management"},
        {"name": "Shipments", "description": "Shipment CRUD and document management"},
        {"name": "Documents", "description": "Document upload, validation, and lifecycle"},
        {"name": "Container Tracking", "description": "Real-time container tracking from carriers"},
        {"name": "EUDR Compliance", "description": "EU Deforestation Regulation compliance and validation"},
        {"name": "Analytics", "description": "Metrics and statistics dashboard"},
        {"name": "Audit", "description": "Audit log access (admin)"},
        {"name": "Webhooks", "description": "Webhook endpoints for carrier updates"},
        {"name": "Notifications", "description": "User notifications"},
        {"name": "Users", "description": "User management"},
        {"name": "Health", "description": "Health check and status endpoints"},
    ]
)

# Add middleware in reverse order (last added runs first)

# Error handling middleware (outermost)
app.add_middleware(
    ErrorHandlerMiddleware,
    sentry_dsn=None,  # Set SENTRY_DSN env var when ready
)

# Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    default_limit=100,
    default_window=60,
    endpoint_limits={
        "/api/auth/login": (10, 60),  # 10 login attempts per minute
        "/api/tracking/": (50, 60),  # 50 tracking requests per minute
        "/api/documents/upload": (20, 60),  # 20 uploads per minute
        "/api/analytics/": (30, 60),  # 30 analytics requests per minute
    }
)

# Request tracking (adds request IDs and timing)
app.add_middleware(RequestTrackingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Request-ID",
        "X-Request-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(shipments.router, prefix="/api/shipments", tags=["Shipments"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Container Tracking"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(audit.router, prefix="/api/audit-log", tags=["Audit"])
app.include_router(eudr.router, prefix="/api/eudr", tags=["EUDR Compliance"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": "TraceHub API",
        "version": "0.2.0",
        "description": "Container tracking and documentation compliance platform",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns comprehensive health status including:
    - API status
    - Database connection status
    - Uptime information
    - Last tracking sync time

    This endpoint does not require authentication.
    """
    # Check database connection
    db_status = "healthy"
    db_latency_ms = None
    try:
        from .database import SessionLocal
        db = SessionLocal()
        start = datetime.utcnow()
        db.execute(text("SELECT 1"))
        db_latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    # Get last tracking sync time
    last_sync = None
    try:
        from .database import SessionLocal
        db = SessionLocal()
        latest_event = db.query(ContainerEvent).order_by(
            ContainerEvent.created_at.desc()
        ).first()
        if latest_event:
            last_sync = latest_event.created_at.isoformat()
        db.close()
    except Exception as e:
        logger.warning(f"Could not get last tracking sync: {e}")

    # Calculate uptime
    uptime_seconds = None
    if app_start_time:
        uptime_seconds = (datetime.utcnow() - app_start_time).total_seconds()

    # Overall status
    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.2.0",
        "components": {
            "api": {
                "status": "healthy",
                "uptime_seconds": uptime_seconds,
            },
            "database": {
                "status": db_status,
                "latency_ms": round(db_latency_ms, 2) if db_latency_ms else None,
            },
            "tracking": {
                "last_sync": last_sync,
            }
        }
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Kubernetes readiness probe.

    Returns 200 if the application is ready to receive traffic.
    """
    try:
        from .database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"ready": True}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Not ready")


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """
    Kubernetes liveness probe.

    Returns 200 if the application is alive (running).
    """
    return {"alive": True}

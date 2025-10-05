"""Health check endpoints."""

from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.db import engine

router = APIRouter()


@router.get("/")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "splunk-auto-doc-api",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness check endpoint with database connectivity verification.
    
    Returns HTTP 200 if ready, HTTP 503 if not ready.
    Checks database connectivity to ensure the service is fully operational.
    """
    checks = {}
    is_ready = True
    
    # Check database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        is_ready = False
    
    response_data = {
        "status": "ready" if is_ready else "not ready",
        "checks": checks,
    }
    
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=response_data, status_code=status_code)

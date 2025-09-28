"""Health check endpoints."""

from typing import Any

from fastapi import APIRouter

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
async def readiness_check() -> dict[str, Any]:
    """Readiness check endpoint (for future database connectivity)."""
    # TODO: Add database connectivity check
    return {
        "status": "ready",
        "checks": {
            "database": "not implemented",
        },
    }
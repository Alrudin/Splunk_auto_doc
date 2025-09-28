"""Health check endpoints for API v1."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint returning required format."""
    return {"status": "ok"}
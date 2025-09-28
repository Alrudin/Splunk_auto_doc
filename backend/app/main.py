"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.config import get_settings
from app.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    print(f"Starting Splunk Auto Doc API v{settings.version}...")

    yield

    # Shutdown
    print("Shutting down Splunk Auto Doc API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Splunk Auto Doc API",
        description="API for parsing and documenting Splunk configurations",
        version=settings.version,
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
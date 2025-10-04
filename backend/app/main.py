"""Main FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.runs import router as runs_router
from app.api.v1.uploads import router as uploads_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.health import router as legacy_health_router

# Initialize logging configuration
settings = get_settings()
setup_logging(log_level=settings.log_level, log_format=settings.log_format)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    logger.info(
        "Starting Splunk Auto Doc API",
        extra={
            "version": settings.version,
            "environment": settings.environment,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "log_format": settings.log_format,
        },
    )

    yield

    # Shutdown
    logger.info("Shutting down Splunk Auto Doc API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Splunk Auto Doc API",
        description="API for parsing and documenting Splunk configurations",
        version=settings.version,
        lifespan=lifespan,
    )

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Include routers
    app.include_router(health_router, prefix="/v1", tags=["health"])
    app.include_router(uploads_router, prefix="/v1", tags=["uploads"])
    app.include_router(runs_router, prefix="/v1", tags=["runs"])
    app.include_router(legacy_health_router, prefix="/health", tags=["health-legacy"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    logger.info("Starting server in development mode")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )

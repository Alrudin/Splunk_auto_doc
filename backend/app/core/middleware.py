"""Request/response logging middleware."""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize middleware."""
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and log details."""
        # Generate correlation ID for request tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Get request size if available
        request_size = request.headers.get("content-length", "0")

        # Record start time
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "request_size": int(request_size) if request_size.isdigit() else 0,
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log exception with full traceback
            duration = time.time() - start_time
            logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                },
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Get response size if available
        response_size = response.headers.get("content-length", "0")

        # Extract run_id from response if present (for upload endpoints)
        run_id = None
        if hasattr(request.state, "run_id"):
            run_id = request.state.run_id

        # Log response
        log_extra = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": round(duration, 4),
            "request_size": int(request_size) if request_size.isdigit() else 0,
            "response_size": int(response_size) if response_size.isdigit() else 0,
        }

        if run_id:
            log_extra["run_id"] = run_id

        logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {duration:.4f}s",
            extra=log_extra,
        )

        # Add request ID to response headers for traceability
        response.headers["X-Request-ID"] = request_id

        return response

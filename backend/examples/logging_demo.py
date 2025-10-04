#!/usr/bin/env python3
"""
Example script showing structured logging output for different scenarios.

This demonstrates:
- Text vs JSON format
- Request/response logging with correlation IDs
- Run ID tracking
- Error logging with tracebacks
"""

import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.logging import setup_logging


def example_text_format():
    """Show text format logging examples."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Text Format Logging")
    print("=" * 70 + "\n")

    setup_logging(log_level="INFO", log_format="text")
    logger = logging.getLogger("app.api.v1.uploads")

    # Simulated upload flow
    print("# Simulated upload request flow:\n")

    logger.info(
        "Received upload request",
        extra={
            "upload_filename": "production_etc.tar.gz",
            "type": "instance_etc",
            "label": "Production Server Config",
        }
    )

    logger.info(
        "Created ingestion run with status=pending",
        extra={"run_id": 42}
    )

    logger.info(
        "File processed",
        extra={
            "run_id": 42,
            "upload_filename": "production_etc.tar.gz",
            "size_bytes": 1024000,
            "sha256": "abc123def456...",
        }
    )

    logger.info(
        "Stored file in storage backend",
        extra={"run_id": 42, "storage_key": "runs/42/production_etc.tar.gz"}
    )

    logger.info(
        "Successfully completed upload for run",
        extra={"run_id": 42, "status": "stored"}
    )


def example_json_format():
    """Show JSON format logging examples."""
    print("\n" + "=" * 70)
    print("EXAMPLE: JSON Format Logging")
    print("=" * 70 + "\n")

    setup_logging(log_level="INFO", log_format="json")
    logger = logging.getLogger("app.core.middleware")

    print("# Request/response logging with correlation ID:\n")

    logger.info(
        "Request started: POST /v1/uploads",
        extra={
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "method": "POST",
            "path": "/v1/uploads",
            "request_size": 1024000,
        }
    )

    logger.info(
        "Request completed: POST /v1/uploads - Status: 201 - Time: 0.8432s",
        extra={
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "method": "POST",
            "path": "/v1/uploads",
            "status_code": 201,
            "duration": 0.8432,
            "request_size": 1024000,
            "response_size": 256,
            "run_id": 42,
        }
    )


def example_error_logging():
    """Show error logging with tracebacks."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Error Logging with Tracebacks")
    print("=" * 70 + "\n")

    setup_logging(log_level="ERROR", log_format="json")
    logger = logging.getLogger("app.api.v1.uploads")

    print("# Error during upload with full context:\n")

    try:
        raise ValueError("Simulated storage failure")
    except ValueError:
        logger.error(
            "Storage error during upload",
            extra={"run_id": 43, "error": "Simulated storage failure"},
            exc_info=True
        )


def example_correlation_tracking():
    """Show correlation ID tracking across logs."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Correlation ID Tracking")
    print("=" * 70 + "\n")

    setup_logging(log_level="INFO", log_format="text")

    print("# Same request_id appears across all log entries:\n")

    middleware_logger = logging.getLogger("app.core.middleware")
    uploads_logger = logging.getLogger("app.api.v1.uploads")

    request_id = "abc-123-def-456"

    middleware_logger.info(
        "Request started: POST /v1/uploads",
        extra={"request_id": request_id, "method": "POST", "path": "/v1/uploads"}
    )

    uploads_logger.info(
        "Received upload request",
        extra={"request_id": request_id, "upload_filename": "test.tar.gz"}
    )

    uploads_logger.info(
        "Created ingestion run with status=pending",
        extra={"request_id": request_id, "run_id": 44}
    )

    middleware_logger.info(
        "Request completed: POST /v1/uploads - Status: 201 - Time: 0.5s",
        extra={
            "request_id": request_id,
            "method": "POST",
            "path": "/v1/uploads",
            "status_code": 201,
            "duration": 0.5,
            "run_id": 44
        }
    )

    print(f"\n→ All entries share request_id='{request_id}' for traceability")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("STRUCTURED LOGGING EXAMPLES")
    print("Configuration: LOG_LEVEL and LOG_FORMAT environment variables")
    print("=" * 70)

    example_text_format()
    example_json_format()
    example_error_logging()
    example_correlation_tracking()

    print("\n" + "=" * 70)
    print("CONFIGURATION GUIDE")
    print("=" * 70)
    print("""
In your .env file:

    # Human-readable format (development)
    LOG_LEVEL=INFO
    LOG_FORMAT=text

    # Machine-parseable format (production)
    LOG_LEVEL=WARNING
    LOG_FORMAT=json

Benefits of JSON format:
- Easy parsing by log aggregators (Splunk, ELK, CloudWatch)
- Structured fields for filtering and searching
- Preserves data types (numbers, booleans)
- Correlation IDs for distributed tracing

Benefits of text format:
- Human-readable during development
- Easy to read in terminal/console
- Better for debugging and local testing
    """)
    print("=" * 70 + "\n")

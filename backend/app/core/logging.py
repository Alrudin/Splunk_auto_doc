"""Structured logging configuration and utilities."""

import json
import logging
import sys
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "request_size"):
            log_data["request_size"] = record.request_size
        if hasattr(record, "response_size"):
            log_data["response_size"] = record.response_size

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", log_format: str = "text") -> None:
    """Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format - 'text' for human-readable or 'json' for structured
    """
    # Get numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    # Set formatter based on format type
    if log_format.lower() == "json":
        formatter = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    else:
        # Human-readable text format
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

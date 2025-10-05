"""Tests for logging middleware and structured logging."""

import json
import logging

import pytest
from app.core.logging import StructuredFormatter, setup_logging
from app.core.middleware import RequestLoggingMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestStructuredFormatter:
    """Tests for the StructuredFormatter class."""

    def test_basic_log_formatting(self):
        """Test that basic log records are formatted as JSON."""
        formatter = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_log_with_extra_fields(self):
        """Test that extra fields are included in JSON output."""
        formatter = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Request completed",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.request_id = "test-request-123"
        record.run_id = 42
        record.duration = 1.234
        record.status_code = 200

        result = formatter.format(record)
        data = json.loads(result)

        assert data["request_id"] == "test-request-123"
        assert data["run_id"] == 42
        assert data["duration"] == 1.234
        assert data["status_code"] == 200

    def test_log_with_exception(self):
        """Test that exceptions are included in JSON output."""
        formatter = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "ERROR"
        assert data["message"] == "Error occurred"
        assert "exception" in data
        assert "ValueError: Test error" in data["exception"]


class TestLoggingSetup:
    """Tests for the setup_logging function."""

    def test_setup_text_logging(self, caplog):
        """Test setting up text-based logging."""
        setup_logging(log_level="INFO", log_format="text")

        logger = logging.getLogger("test.text")
        logger.info("Test message")

        # Check that logging is configured
        assert len(caplog.records) > 0 or logging.getLogger().handlers

    def test_setup_json_logging(self):
        """Test setting up JSON-based logging."""
        setup_logging(log_level="DEBUG", log_format="json")

        # Verify handler is configured with StructuredFormatter
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)

    def test_log_level_configuration(self):
        """Test that log level is properly configured."""
        setup_logging(log_level="WARNING", log_format="text")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING


class TestRequestLoggingMiddleware:
    """Tests for the RequestLoggingMiddleware."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI application with middleware."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        # Add middleware
        app.add_middleware(RequestLoggingMiddleware)

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_successful_request_logging(self, client, caplog):
        """Test that successful requests are logged properly."""
        with caplog.at_level(logging.INFO):
            response = client.get("/test")

        assert response.status_code == 200

        # Check for request start and completion logs
        log_messages = [record.message for record in caplog.records]
        assert any("Request started" in msg for msg in log_messages)
        assert any("Request completed" in msg for msg in log_messages)

    def test_request_id_in_response_header(self, client):
        """Test that X-Request-ID header is added to response."""
        response = client.get("/test")

        assert "X-Request-ID" in response.headers
        # Should be a valid UUID format
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0
        assert "-" in request_id  # UUIDs contain hyphens

    def test_error_request_logging(self, client, caplog):
        """Test that failed requests log exceptions."""
        with caplog.at_level(logging.ERROR), pytest.raises(
            ValueError, match="Test error"
        ):
            client.get("/error")

        # Verify the middleware logged the error
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) > 0

        # Check that our middleware logged the error
        middleware_logs = [log for log in error_logs if "Request failed" in log.message]
        assert len(middleware_logs) > 0

        # Check for error log with exception
        log_messages = [record.message for record in caplog.records]
        assert any("Request failed" in msg for msg in log_messages)

        # Check that exception info is captured
        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(error_records) > 0
        assert any(r.exc_info for r in error_records)

    def test_request_logging_includes_method_and_path(self, client, caplog):
        """Test that logs include HTTP method and path."""
        with caplog.at_level(logging.INFO):
            client.get("/test")

        # Find the completion log
        completion_logs = [
            r for r in caplog.records if "Request completed" in r.message
        ]
        assert len(completion_logs) > 0

        # Check for extra fields
        log_record = completion_logs[0]
        assert hasattr(log_record, "method")
        assert log_record.method == "GET"
        assert hasattr(log_record, "path")
        assert log_record.path == "/test"
        assert hasattr(log_record, "status_code")
        assert log_record.status_code == 200
        assert hasattr(log_record, "duration")


def test_logging_configuration_import():
    """Test that logging modules can be imported."""
    from app.core.logging import StructuredFormatter, setup_logging
    from app.core.middleware import RequestLoggingMiddleware

    assert setup_logging is not None
    assert StructuredFormatter is not None
    assert RequestLoggingMiddleware is not None


if __name__ == "__main__":
    # Run basic validation
    test_logging_configuration_import()
    print("✅ Logging configuration tests ready")

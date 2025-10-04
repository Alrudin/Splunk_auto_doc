# Structured Logging & Request Middleware - Implementation Summary

## Overview
This implementation adds comprehensive structured logging and request middleware to the Splunk Auto Doc FastAPI application, fulfilling the requirements specified in the Milestone-1 gap analysis.

## Features Implemented

### 1. Configurable Logging System
- **Configuration via Environment Variables**:
  - `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
  - `LOG_FORMAT`: text (human-readable) or json (structured) (default: text)

### 2. Structured Logging Formatter
- **Text Format**: Human-readable with pipe separators for development
  ```
  2025-10-04 09:07:23 | INFO | app.core.middleware | Request completed: POST /v1/uploads - Status: 201 - Time: 0.8432s
  ```

- **JSON Format**: Structured data for log aggregators
  ```json
  {"timestamp": "2025-10-04 09:07:23", "level": "INFO", "logger": "app.core.middleware", "message": "Request completed", "request_id": "abc-123", "run_id": 42, "status_code": 201}
  ```

### 3. Request/Response Logging Middleware
- **Automatic Request Tracing**:
  - Unique correlation ID (UUID) for each request
  - Logged at request start and completion
  - Included in response header as `X-Request-ID`

- **Comprehensive Metrics**:
  - HTTP method and path
  - Request/response sizes (when available)
  - Response status code
  - Request duration (in seconds)
  - Ingestion run ID (for upload operations)

### 4. Exception Handling
- Full tracebacks captured with `exc_info=True`
- Structured error context (run_id, error message, etc.)
- Both text and JSON formats preserve exception details

### 5. Application Lifecycle Logging
- **Startup Events**:
  - Application version
  - Environment (development/staging/production)
  - Debug mode status
  - Logging configuration

- **Shutdown Events**:
  - Clean shutdown logging

### 6. Upload Endpoint Integration
- All upload operations log with structured fields
- Run ID automatically tracked and correlated
- File metadata logged (size, SHA256, storage key)
- Error context preserved during failures

## Files Modified/Created

### Core Implementation
- `backend/app/core/logging.py` - Structured logging formatter and setup
- `backend/app/core/middleware.py` - Request logging middleware
- `backend/app/core/config.py` - Added LOG_LEVEL and LOG_FORMAT settings
- `backend/app/main.py` - Integrated logging system and middleware
- `backend/app/api/v1/uploads.py` - Enhanced with structured logging

### Documentation
- `README.md` - Added comprehensive logging section with:
  - Configuration guide
  - Format examples
  - Request tracing explanation
  - Docker and local development log viewing
  - Production recommendations

- `.env.example` - Added logging configuration variables

### Testing & Examples
- `backend/tests/test_logging.py` - Comprehensive test suite:
  - StructuredFormatter tests
  - setup_logging tests
  - RequestLoggingMiddleware tests

- `backend/examples/logging_demo.py` - Working examples showing:
  - Text format logging
  - JSON format logging
  - Error logging with tracebacks
  - Correlation ID tracking

## Configuration

### Environment Variables (.env)
```bash
# Development (human-readable)
LOG_LEVEL=INFO
LOG_FORMAT=text

# Production (machine-parseable)
LOG_LEVEL=WARNING
LOG_FORMAT=json
```

## Usage Examples

### Viewing Logs in Docker
```bash
# Follow logs from API service
docker compose logs -f api

# View last 100 lines
docker compose logs --tail=100 api
```

### Viewing Logs Locally
```bash
# Logs output to stdout/stderr
python backend/app/main.py

# Or via uvicorn
uvicorn app.main:app --reload
```

### Tracing Requests
Each HTTP request receives a correlation ID that appears in:
1. Request start log
2. All application logs during request processing
3. Request completion log
4. Response header: `X-Request-ID`

Example:
```bash
curl -X POST http://localhost:8000/v1/uploads \
  -F "file=@test.tar.gz" \
  -F "type=instance_etc" \
  -v | grep X-Request-ID
```

## Log Fields Reference

### Standard Fields (All Logs)
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Logger name (module path)
- `message`: Human-readable message

### Request/Response Fields
- `request_id`: Unique correlation ID (UUID)
- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `status_code`: HTTP status code
- `duration`: Request duration in seconds
- `request_size`: Request body size in bytes
- `response_size`: Response body size in bytes

### Upload Operation Fields
- `run_id`: Ingestion run ID
- `upload_filename`: Name of uploaded file
- `size_bytes`: File size in bytes
- `sha256`: SHA256 hash of file
- `storage_key`: Storage backend key/path
- `type`: Upload type (ds_etc, instance_etc, etc.)
- `label`: Optional human-readable label

### Error Fields
- `error`: Error message
- `exception`: Full traceback (when available)

## Testing

### Run Test Suite
```bash
cd backend
pytest tests/test_logging.py -v
```

### Run Demo Script
```bash
cd backend
python3 examples/logging_demo.py
```

## Production Recommendations

1. **Use JSON Format**: Easier parsing by log aggregators (Splunk, ELK, CloudWatch)
2. **Set Appropriate Log Level**: WARNING or INFO for production
3. **Forward Logs**: Send to centralized logging infrastructure
4. **Monitor Correlation IDs**: Trace request flows across services
5. **Alert on Errors**: Set up alerts for ERROR and CRITICAL level logs

## Benefits

### For Development
- Human-readable logs with text format
- Easy debugging with correlation IDs
- Clear error tracebacks
- Request flow visibility

### For Production
- Structured JSON logs for aggregators
- Performance metrics (request duration)
- Error tracking with context
- Distributed tracing via correlation IDs
- Compliance and audit trails

## Compliance with Requirements

This implementation fully addresses the issue requirements:

✅ Request/response logging middleware
- Logs HTTP method, path, status, duration
- Logs request/response size
- Logs correlation ID and run ID

✅ Structured logging
- JSON format for machine parsing
- Text format for human reading
- Consistent field names

✅ Configurable via environment
- LOG_LEVEL and LOG_FORMAT settings
- Not hardcoded, follows best practices

✅ Startup and shutdown events logged
- Version, environment, debug mode
- Clean shutdown messages

✅ Error and exception logging
- Full tracebacks captured
- Contextual information preserved

✅ Documentation
- README section on logging
- Examples and usage patterns
- Configuration guide
- Production recommendations

## Future Enhancements

Potential improvements for later milestones:
- Log rotation configuration
- Async logging for high-throughput scenarios
- Integration with distributed tracing systems (OpenTelemetry)
- Performance metrics dashboards
- Log sampling for high-volume endpoints

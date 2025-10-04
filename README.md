# Splunk Auto Doc

## Overview

Splunk Auto Doc is a web application that parses and analyzes Splunk configuration files to generate comprehensive documentation and visualizations. The tool helps Splunk administrators understand data flow, configuration dependencies, and routing paths within their Splunk deployments.

Key features:
- **Configuration Parsing**: Extracts and normalizes Splunk configuration files (inputs.conf, props.conf, transforms.conf, etc.)
- **Serverclass Resolution**: Resolves deployment server configurations to determine host memberships and app assignments
- **Data Flow Analysis**: Traces data routing from inputs through transforms to final destinations
- **Interactive Visualization**: Provides web-based exploration of configuration relationships and data paths
- **Version Tracking**: Maintains historical snapshots of configuration changes through ingestion runs

## Stack

### Backend
- **Python 3.11+** - Core runtime
- **FastAPI** - REST API framework with automatic OpenAPI documentation
- **Pydantic v2** - Data validation and serialization
- **SQLAlchemy/SQLModel** - Database ORM and query builder
- **PostgreSQL 15+** - Primary data store
- **Alembic** - Database migration management
- **Celery + Redis** - Background task processing (future milestone)

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and development server
- **TailwindCSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **React Query** - Server state management
- **d3.js/Cytoscape.js** - Data visualization and graph rendering

### Infrastructure
- **Docker Compose** - Local development orchestration
- **MinIO** - S3-compatible object storage for file uploads
- **Ruff** - Python linting and formatting
- **mypy** - Static type checking
- **pytest** - Testing framework
- **pre-commit** - Git hooks for code quality

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alrudin/Splunk_auto_doc.git
   cd Splunk_auto_doc
   ```

2. **Start the development environment**
   ```bash
   # Start all services with Docker Compose
   docker compose up -d
   
   # Or use the Makefile
   make docker-up
   ```

3. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend: http://localhost:3000
   - MinIO Console: http://localhost:9001 (admin/password)

### Local Development

1. **Backend setup**
   ```bash
   # Install Python dependencies
   pip install -e ".[dev]"
   
   # Set up pre-commit hooks
   pre-commit install
   
   # Run the API server (option 1)
   make api
   
   # Run the API server (option 2)
   cd backend
   python -m app.main
   
   # Run the API server (option 3)
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend setup**
   ```bash
   # Navigate to frontend directory
   cd frontend
   
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   
   # Build for production
   npm run build
   
   # Run linter
   npm run lint
   ```

3. **Database setup**
   ```bash
   # Run database migrations
   cd backend
   alembic upgrade head
   
   # Check current migration version
   alembic current
   
   # View migration history
   alembic history
   ```

4. **Run tests**
   ```bash
   # Run all tests
   pytest backend/tests/
   
   # Run with coverage
   pytest backend/tests/ --cov=backend/app
   ```

5. **Code quality checks**
   ```bash
   # Format code
   ruff format backend/
   
   # Run linter
   ruff check backend/
   
   # Type checking
   mypy backend/app/
   ```

### API Usage Example

```bash
# Health check (v1 endpoint)
curl http://localhost:8000/v1/health

# Health check (legacy endpoint)
curl http://localhost:8000/health/

# Upload Splunk configuration
curl -X POST "http://localhost:8000/v1/uploads" \
     -F "file=@splunk_etc.tar.gz" \
     -F "type=ds_etc" \
     -F "label=Production Deployment Server" \
     -F "notes=Weekly configuration backup"

# Upload with minimal parameters
curl -X POST "http://localhost:8000/v1/uploads" \
     -F "file=@my_app.tar.gz" \
     -F "type=app_bundle"

# List ingestion runs (future milestone)
curl http://localhost:8000/v1/runs
```

## Database Schema

### Core Tables

The application uses PostgreSQL for persistent storage with Alembic for migration management.

**ingestion_runs** - Tracks uploaded configuration bundles
- `id` (integer, primary key) - Unique identifier
- `created_at` (timestamp) - Creation timestamp
- `type` (enum) - Upload type: `ds_etc`, `instance_etc`, `app_bundle`, `single_conf`
- `label` (string, nullable) - Optional human-readable label
- `status` (enum) - Processing status: `pending`, `stored`, `failed`, `complete`
- `notes` (text, nullable) - Optional notes

**files** - Tracks uploaded files within ingestion runs
- `id` (integer, primary key) - Unique identifier
- `run_id` (integer, foreign key) - References `ingestion_runs.id`
- `path` (string) - Archive filename or file path
- `sha256` (string) - SHA256 hash for deduplication
- `size_bytes` (bigint) - File size in bytes
- `stored_object_key` (string) - Blob storage reference

### Running Migrations

Migrations are managed with Alembic and located in `backend/alembic/versions/`.

```bash
# Apply all pending migrations
cd backend
alembic upgrade head

# Revert last migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

For development, ensure PostgreSQL is running (via Docker Compose) before applying migrations.

## Logging & Monitoring

### Logging Configuration

The application supports structured logging with configurable output formats and levels. Logging behavior is controlled via environment variables in `.env`:

**Configuration Options:**
- `LOG_LEVEL` - Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: `INFO`)
- `LOG_FORMAT` - Output format: `text` (human-readable) or `json` (structured JSON) (default: `text`)

**Example `.env` configuration:**
```bash
LOG_LEVEL=INFO
LOG_FORMAT=text
```

### Log Output Formats

**Text Format (Human-Readable):**
```
2025-01-15 10:30:45 | INFO | app.main | Starting Splunk Auto Doc API
2025-01-15 10:30:46 | INFO | app.core.middleware | Request completed: POST /v1/uploads - Status: 201 - Time: 0.1234s
```

**JSON Format (Structured):**
```json
{"timestamp": "2025-01-15 10:30:45", "level": "INFO", "logger": "app.main", "message": "Starting Splunk Auto Doc API", "version": "0.1.0", "environment": "development"}
{"timestamp": "2025-01-15 10:30:46", "level": "INFO", "logger": "app.core.middleware", "message": "Request completed: POST /v1/uploads - Status: 201 - Time: 0.1234s", "request_id": "abc-123", "method": "POST", "path": "/v1/uploads", "status_code": 201, "duration": 0.1234, "run_id": 42}
```

### Request Tracing

Each HTTP request is assigned a unique **correlation ID** (`request_id`) for end-to-end tracing:
- Logged with request start/completion entries
- Returned in response header: `X-Request-ID`
- Linked to ingestion run IDs when applicable (`run_id` field)

**Example request flow:**
```bash
# Make a request
curl -X POST http://localhost:8000/v1/uploads -F "file=@test.tar.gz" -F "type=instance_etc" -v

# Response includes correlation ID in headers
< X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Log entries for the request:**
```
2025-01-15 10:30:45 | INFO | app.core.middleware | Request started: POST /v1/uploads
2025-01-15 10:30:46 | INFO | app.core.middleware | Request completed: POST /v1/uploads - Status: 201 - Time: 0.1234s
```

### Logged Information

**Startup/Shutdown Events:**
- Application version, environment, debug mode, log configuration

**HTTP Requests (via middleware):**
- HTTP method and path
- Request/response sizes (when available)
- Status code and duration
- Correlation ID (`request_id`)
- Ingestion run ID (`run_id`) for upload operations
- Exception tracebacks for failed requests

### Viewing Logs

**Docker Compose:**
```bash
# View logs from API service
docker compose logs -f api

# View logs with timestamps
docker compose logs -f --timestamps api

# View last 100 lines
docker compose logs --tail=100 api
```

**Local Development:**
```bash
# Logs are written to stdout/stderr
python backend/app/main.py

# Or via uvicorn
uvicorn app.main:app --reload
```

### Production Recommendations

For production deployments:
1. **Use JSON format** (`LOG_FORMAT=json`) for easier parsing by log aggregators (ELK, Splunk, CloudWatch)
2. **Set appropriate log level** (`LOG_LEVEL=WARNING` or `LOG_LEVEL=INFO`)
3. **Forward logs** to centralized logging infrastructure
4. **Monitor correlation IDs** to trace request flows across services

---

**Current Status**: Milestone 1 - Project skeleton and upload ingestion foundation in progress.
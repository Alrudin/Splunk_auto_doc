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

### Development Tooling
**Backend:**
- **Ruff** - Python linting and formatting
- **mypy** - Static type checking
- **pytest** - Testing framework
- **pre-commit** - Git hooks for code quality

**Frontend:**
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **Vitest** - Unit testing framework
- **TypeScript** - Type checking

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
   # Run all tests (backend)
   make test

   # Run backend tests only
   make test-backend
   # or
   pytest backend/tests/

   # Run frontend tests only
   make test-frontend
   # or
   cd frontend && npm run test

   # Run tests with coverage report
   make test-coverage

   # Run with coverage (backend only)
   pytest backend/tests/ --cov=backend/app --cov-report=term --cov-report=html

   # Run with coverage (frontend only)
   cd frontend && npm run test:coverage
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

## Testing

This project has comprehensive test coverage for both backend and frontend.

### Backend Testing

**Framework:** pytest with pytest-cov for coverage

**Test Structure:**
- `backend/tests/` - All backend tests
- `backend/tests/conftest.py` - Shared pytest fixtures
- Unit tests for models, schemas, storage, and API endpoints
- Integration tests for upload lifecycle and database operations

**Test Categories:**
- **Unit Tests:** Individual component behavior (models, schemas, endpoints)
- **Integration Tests:** End-to-end workflows (upload lifecycle, storage operations)
- **Error Handling Tests:** Edge cases, validation, failure scenarios

**Running Backend Tests:**
```bash
# Run all backend tests
make test-backend

# Run specific test file
pytest backend/tests/test_uploads.py -v

# Run with coverage
pytest backend/tests/ --cov=backend/app --cov-report=term --cov-report=html

# Run specific test class
pytest backend/tests/test_uploads.py::TestUploadEndpoint -v

# Run specific test
pytest backend/tests/test_uploads.py::TestUploadEndpoint::test_upload_success -v

# Run tests matching a pattern
pytest backend/tests/ -k "upload" -v

# Run with detailed output
pytest backend/tests/ -vv --tb=short
```

**Running Tests with Docker:**
```bash
# Run all backend tests in Docker container
docker compose run --rm api pytest tests/ -v

# Run with coverage in Docker
docker compose run --rm api pytest tests/ --cov=app --cov-report=term

# Run specific test file in Docker
docker compose run --rm api pytest tests/test_uploads.py -v

# Validate test structure without running tests
python backend/tests/validate_tests.py
```

**Test Fixtures:**
The `conftest.py` provides shared fixtures:
- `test_db` - In-memory SQLite database for isolated tests
- `test_storage` - Temporary directory storage backend
- `client` - FastAPI TestClient with overridden dependencies
- `db_session` - Direct database session access
- `sample_tar_file` - Sample file for upload tests
- `sample_upload_metadata` - Sample metadata for tests
- `large_file` - Large file (5MB) for performance testing
- `sample_files` - Multiple sample files for batch testing

**Upload Lifecycle Test Coverage:**
- ✅ Successful file upload and storage
- ✅ Database record creation (ingestion_runs and files tables)
- ✅ SHA256 hash computation and verification
- ✅ Metadata accuracy (type, label, notes)
- ✅ Blob retrievability from storage
- ✅ Multiple sequential uploads
- ✅ Large file handling (1MB-10MB)
- ✅ Empty file handling
- ✅ Invalid ingestion type validation
- ✅ Missing metadata validation
- ✅ Storage failure scenarios
- ✅ Special characters in filenames
- ✅ End-to-end integration tests
- ✅ Incremental ingestion scenarios

**Coverage Goals:**
- Minimum 70% coverage for touched/modified code
- Critical paths (uploads, runs, storage) should have >80% coverage
- All API endpoints should have at least basic integration tests

### Frontend Testing

**Framework:** Vitest with React Testing Library

**Test Structure:**
- `frontend/src/test/` - Test files and setup
- `frontend/src/test/setup.ts` - Test configuration
- `frontend/vitest.config.ts` - Vitest configuration
- Unit tests for components and API client
- Integration tests for routing and navigation

**Running Frontend Tests:**
```bash
# Run all frontend tests
make test-frontend
# or
cd frontend && npm run test

# Run with UI (interactive mode)
cd frontend && npm run test:ui

# Run with coverage
cd frontend && npm run test:coverage
```

**Test Files:**
- `App.test.ts` - Basic application tests
- `HomePage.test.tsx` - HomePage component tests
- `MainLayout.test.tsx` - Layout component tests
- `ApiClient.test.ts` - API client wrapper tests
- `Navigation.test.tsx` - Routing integration tests

**Coverage Configuration:**
Coverage reports exclude:
- `node_modules/`
- `src/test/`
- `**/*.d.ts`
- `**/*.config.*`
- `dist/`

### Running All Tests

```bash
# Run both backend and frontend tests
make test

# Run with coverage reports for both
make test-coverage
```

### Troubleshooting Tests

**Backend:**

1. **Dependencies not available** - Install with `pip install -e ".[dev]"`
2. **Database errors** - Tests use in-memory SQLite, no external DB needed
3. **Import errors** - Ensure you're in the project root directory

**Frontend:**

1. **Dependencies not installed** - Run `cd frontend && npm install`
2. **Module not found** - Check that all imports use correct paths
3. **Component test failures** - Ensure components are wrapped in proper context (Router, etc.)

**Common Issues:**

- **Timeout errors**: Some tests may need longer timeouts for async operations
- **Port conflicts**: Ensure no services are running on test ports
- **File permissions**: Temporary test directories need write permissions

### Writing New Tests

**Backend Test Example:**
```python
def test_my_feature(client, test_db):
    """Test my new feature."""
    response = client.get("/v1/my-endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

**Frontend Test Example:**
```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import MyComponent from '../components/MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(
      <BrowserRouter>
        <MyComponent />
      </BrowserRouter>
    )
    expect(screen.getByText('Expected Text')).toBeDefined()
  })
})
```

### Continuous Integration

Tests are run in CI on every pull request. Coverage reports are generated and must meet minimum thresholds (70% for touched code).

## Development Tools & Pre-Commit Hooks

### Tooling Overview

This project uses a comprehensive set of tools to maintain code quality:

**Backend (Python)**
- **Ruff** - Fast Python linter and formatter (replaces flake8, black, isort)
- **mypy** - Static type checker for Python
- **pytest** - Testing framework with coverage support

**Frontend (TypeScript/React)**
- **ESLint** - JavaScript/TypeScript linter
- **Prettier** - Code formatter
- **Vitest** - Fast unit test framework (Vite-native alternative to Jest)
- **TypeScript** - Static type checking

### Installing Development Tools

**Backend tooling:**
```bash
# Install all Python development dependencies
pip install -e ".[dev]"

# This includes: ruff, mypy, pytest, pytest-asyncio, pytest-cov, pre-commit
```

**Frontend tooling:**
```bash
cd frontend
npm install

# This includes: eslint, prettier, vitest, typescript, and their plugins
```

### Running Quality Checks

**Backend:**
```bash
# Format Python code
make format
# or
ruff format backend/

# Lint Python code
make lint
# or
ruff check backend/

# Type check Python code
make type-check
# or
mypy backend/app/

# Run Python tests
make test
# or
pytest backend/tests/ -v

# Run tests with coverage
pytest backend/tests/ --cov=backend/app
```

**Frontend:**
```bash
cd frontend

# Lint TypeScript/React code
npm run lint

# Format code with Prettier
npm run format

# Check formatting (CI mode)
npm run format:check

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Build TypeScript
npm run build
```

### Pre-Commit Hooks

Pre-commit hooks automatically run quality checks before each commit to catch issues early.

**Installation:**
```bash
# Install pre-commit hooks (run once after cloning)
pip install -e ".[dev]"
pre-commit install

# Or if you have pre-commit installed separately:
pre-commit install
```

**What gets checked:**
- **Python files**: Ruff linting & formatting, mypy type checking, pytest tests
- **TypeScript files**: ESLint linting, Prettier formatting, Vitest tests
- **All files**: Trailing whitespace, EOF fixes, YAML/JSON/TOML validation

**Running hooks manually:**
```bash
# Run on all files (useful after installation or updates)
pre-commit run --all-files

# Run on staged files only (this happens automatically on commit)
pre-commit run

# Skip hooks for a specific commit (not recommended)
git commit --no-verify -m "message"
```

**Updating hooks:**
```bash
# Update hook versions to latest
pre-commit autoupdate

# Clean hook cache
pre-commit clean
```

### Troubleshooting

**Pre-commit hook failures:**

1. **"pytest not found"** - Install backend dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. **"npm run lint failed"** - Install frontend dependencies:
   ```bash
   cd frontend && npm install
   ```

3. **Type errors from mypy** - Fix the reported type issues or add type ignores:
   ```python
   # type: ignore[error-code]
   ```

4. **Formatting issues** - Auto-fix with formatters:
   ```bash
   # Backend
   ruff format backend/

   # Frontend
   cd frontend && npm run format
   ```

5. **Test failures** - Fix failing tests before committing:
   ```bash
   # Backend
   pytest backend/tests/ -v

   # Frontend
   cd frontend && npm run test
   ```

**Skipping specific hooks temporarily:**
```bash
# Set SKIP environment variable
SKIP=eslint,prettier git commit -m "WIP: work in progress"

# Skip all hooks (use sparingly)
git commit --no-verify -m "Emergency fix"
```

**CI/CD behavior:**
The CI pipeline runs the same checks as pre-commit hooks plus additional integration tests. All checks must pass for PRs to be merged.


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

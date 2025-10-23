# Splunk Auto Doc

[![Backend CI](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/frontend-ci.yml)

## Overview

Splunk Auto Doc is a web application that parses and analyzes Splunk configuration files to generate comprehensive documentation and visualizations. The tool helps Splunk administrators understand data flow, configuration dependencies, and routing paths within their Splunk deployments.

Key features:
- **Configuration Parsing**: Extracts and normalizes Splunk configuration files (inputs.conf, props.conf, transforms.conf, etc.)
- **Asynchronous Processing**: Background workers handle parsing jobs with retry logic and progress tracking
- **Provenance Tracking**: Full metadata capture for all parsed configurations (app, scope, layer, file)
- **Serverclass Resolution**: Resolves deployment server configurations to determine host memberships and app assignments (future)
- **Data Flow Analysis**: Traces data routing from inputs through transforms to final destinations (future)
- **Interactive Visualization**: Provides web-based exploration of configuration relationships and data paths (future)
- **Version Tracking**: Maintains historical snapshots of configuration changes through ingestion runs

## Architecture (Milestone 2)

**Current Milestone Scope:**
Milestone 2 builds on the foundation with asynchronous parsing and normalization. The architecture now includes:

1. **Upload Ingestion**: Accept and validate Splunk configuration archives (tar/zip)
2. **Blob Storage**: Store raw configuration files in object storage (MinIO or local filesystem)
3. **Background Worker**: Asynchronous parsing with Celery and Redis
4. **Configuration Parsing**: Extract and parse .conf files from archives
5. **Data Normalization**: Store parsed stanzas with full provenance metadata
6. **REST API**: Endpoints for upload, parsing status, worker health, and retrieval
7. **Web Interface**: React-based UI for uploading files and viewing ingestion runs

**Components:**

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Upload Page  │  │  Runs Page   │  │  (Future: View)  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Endpoints: /v1/uploads, /v1/runs, /v1/health,  │   │
│  │                 /v1/worker/health                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │   Service    │  │   Storage    │  │   Middleware   │    │
│  │    Layer     │  │  Abstraction │  │   (Logging)    │    │
│  └──────────────┘  └──────────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────────┘
            ↓                      ↓              ↓
┌─────────────────────┐  ┌──────────────────────┐  ┌────────────┐
│   PostgreSQL        │  │  MinIO/Object Store  │  │   Redis    │
│  (Metadata DB)      │  │  (File Blobs)        │  │  (Queue)   │
│  - ingestion_runs   │  │  - .tar.gz archives  │  │            │
│  - files            │  │                      │  │            │
│  - stanzas          │  │                      │  │            │
└─────────────────────┘  └──────────────────────┘  └────────────┘
            ↑                      ↑                      ↑
            └──────────────────────┴──────────────────────┘
                    ┌──────────────────────────────┐
                    │   Celery Worker Service      │
                    │  ┌────────────────────────┐  │
                    │  │  parse_run(run_id)     │  │
                    │  │  - Extract archives    │  │
                    │  │  - Parse .conf files   │  │
                    │  │  - Persist stanzas     │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
```

**Data Flow:**
1. User uploads configuration archive via web UI
2. API validates file and metadata
3. File is streamed to object storage (SHA256 hash computed)
4. Metadata is persisted to PostgreSQL (run and file records)
5. **Parsing task is enqueued to Redis** (NEW)
6. **Worker picks up task and processes archive** (NEW)
7. **Worker extracts and parses .conf files** (NEW)
8. **Parsed stanzas stored in database with provenance** (NEW)
9. Run status updated to COMPLETE or FAILED
10. User can monitor parsing progress and view results

**Future Milestones** will add:
- Host and app resolution from serverclass configs
- Data path computation and visualization
- Advanced projections and queries

See [`notes/milestone-1-plan.md`](notes/milestone-1-plan.md) for detailed milestone specifications.

## Stack

### Backend
- **Python 3.11+** - Core runtime
- **FastAPI** - REST API framework with automatic OpenAPI documentation
- **Pydantic v2** - Data validation and serialization
- **SQLAlchemy/SQLModel** - Database ORM and query builder
- **PostgreSQL 15+** - Primary data store
- **Alembic** - Database migration management
- **Celery + Redis** - Background task processing for asynchronous parsing

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
   - Worker Health: http://localhost:8000/v1/worker/health
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
- `backend/tests/test_worker_integration.py` - Worker and parsing task tests

**Test Categories:**
- **Unit Tests:** Individual component behavior (models, schemas, endpoints)
- **Integration Tests:** End-to-end workflows (upload lifecycle, storage operations, worker tasks)
- **Worker Tests:** Background task execution, parsing, retry logic
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

Our CI/CD pipeline automatically runs quality checks on every push and pull request to ensure code quality and prevent regressions.

**CI Workflows:**
- **Backend CI** [![Backend CI](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/backend-ci.yml)
  - Runs on: Python 3.11 and 3.12
  - Steps: Ruff linting → Ruff format check → mypy type checking → pytest with coverage
  - All steps must pass for PR approval

- **Frontend CI** [![Frontend CI](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/frontend-ci.yml)
  - Runs on: Node.js 20
  - Steps: ESLint linting → Prettier format check → TypeScript build → Vitest tests with coverage
  - All steps must pass for PR approval

**What Gets Checked:**
- **Linting**: Code style and quality issues (Ruff for Python, ESLint for TypeScript)
- **Formatting**: Code formatting consistency (Ruff for Python, Prettier for TypeScript)
- **Type Checking**: Static type validation (mypy for Python, TypeScript compiler for frontend)
- **Testing**: Unit and integration tests with coverage reports (pytest for backend, Vitest for frontend)

**Coverage Requirements:**
- Minimum 70% coverage for touched/modified code
- Critical paths (uploads, runs, storage) should have >80% coverage
- Coverage reports are uploaded to the CI logs

**Troubleshooting CI Failures:**

*Backend CI Failures:*

1. **Ruff linting errors**
   ```bash
   # Fix automatically where possible
   ruff check backend/ --fix

   # Check what needs manual fixing
   ruff check backend/
   ```

2. **Ruff format errors**
   ```bash
   # Format all backend code
   ruff format backend/
   ```

3. **mypy type errors**
   ```bash
   # Run mypy locally to see errors
   mypy backend/app/

   # Common fixes:
   # - Add type hints to function parameters and return types
   # - Import types from typing module
   # - Use proper type annotations for variables
   ```

4. **pytest failures**
   ```bash
   # Run tests locally with verbose output
   pytest backend/tests/ -v

   # Run specific failing test
   pytest backend/tests/test_file.py::test_name -v

   # Run with coverage to identify untested code
   pytest backend/tests/ --cov=backend/app --cov-report=term
   ```

*Frontend CI Failures:*

1. **ESLint errors**
   ```bash
   cd frontend

   # Fix automatically where possible
   npm run lint -- --fix

   # Check what needs manual fixing
   npm run lint
   ```

2. **Prettier format errors**
   ```bash
   cd frontend

   # Format all frontend code
   npm run format

   # Check formatting
   npm run format:check
   ```

3. **TypeScript build errors**
   ```bash
   cd frontend

   # Run build to see type errors
   npm run build

   # Common fixes:
   # - Add proper type annotations
   # - Fix import paths
   # - Update component props types
   ```

4. **Vitest test failures**
   ```bash
   cd frontend

   # Run tests locally
   npm run test

   # Run specific test file
   npm run test -- src/test/ComponentName.test.tsx

   # Run with UI for debugging
   npm run test:ui
   ```

*General Tips:*
- Always run quality checks locally before pushing: `pre-commit run --all-files`
- Check CI logs for detailed error messages
- Ensure all dependencies are up to date
- If CI passes but pre-commit fails (or vice versa), check tool versions match

**CI Secrets and Environment Variables:**

The CI workflows are designed to run without requiring any secrets or environment variables. All quality checks (linting, type checking, testing) run using only the code in the repository.

*Optional Configuration:*
- **CODECOV_TOKEN**: If you want to upload coverage reports to Codecov, add this secret to your GitHub repository settings. The CI workflows will continue to work without it, as the codecov upload step uses `continue-on-error: true`.

*Security Notes:*
- No sensitive information (API keys, passwords, database credentials) is used in CI
- All tests use in-memory databases or temporary file storage
- Test fixtures are self-contained and don't require external services
- Coverage reports contain only code statistics, no sensitive data

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


### API Usage Examples

All API endpoints are documented interactively at http://localhost:8000/docs (OpenAPI/Swagger UI).

**Health Check:**
```bash
# Health check endpoint
curl http://localhost:8000/v1/health

# Example response:
# {"status":"ok","timestamp":"2025-01-15T10:30:45.123456Z","version":"1.0.0"}
```

**Upload Splunk Configuration:**
```bash
# Upload with all metadata
curl -X POST "http://localhost:8000/v1/uploads" \
     -F "file=@splunk_etc.tar.gz" \
     -F "type=ds_etc" \
     -F "label=Production Deployment Server" \
     -F "notes=Weekly configuration backup"

# Upload with minimal parameters
curl -X POST "http://localhost:8000/v1/uploads" \
     -F "file=@my_app.tar.gz" \
     -F "type=app_bundle"

# Example response:
# {
#   "run_id": 42,
#   "status": "stored",
#   "created_at": "2025-01-15T10:30:45.123456Z",
#   "type": "ds_etc",
#   "label": "Production Deployment Server",
#   "notes": "Weekly configuration backup"
# }
```

**Valid upload types:**
- `ds_etc` - Deployment Server etc directory
- `instance_etc` - Splunk instance etc directory
- `app_bundle` - Splunk app bundle
- `single_conf` - Single configuration file

**Memory-Safe Streaming Upload:**

The upload endpoint is designed to handle files of any size safely:

- **Streaming Processing**: Files are streamed in 8KB chunks, never loaded fully into memory
- **Incremental Hashing**: SHA256 hash is computed as chunks are processed, not after full read
- **Efficient Storage**: Both local filesystem and S3 backends use chunked writes
- **No Memory Limits**: Can safely handle files >1GB without memory exhaustion
- **Production Ready**: Tested with files up to 500MB in automated tests

**Memory Safety Guarantees:**
- Maximum memory overhead per upload: ~16KB (2x chunk size for buffering)
- Hash computation uses constant memory regardless of file size
- Storage backends use `shutil.copyfileobj()` (local) and `upload_fileobj()` (S3) for efficient streaming
- No temporary file creation on the API server

**Limitations:**
- Upload size limited by web server/proxy configuration (default: no application limit)
- Network timeout may affect very large uploads over slow connections
- Disk space must be available on storage backend

**List Ingestion Runs:**
```bash
# List all runs (default: page 1, 50 per page)
curl http://localhost:8000/v1/runs

# List with pagination
curl "http://localhost:8000/v1/runs?page=1&per_page=20"

# Example response:
# {
#   "runs": [
#     {
#       "id": 42,
#       "created_at": "2025-01-15T10:30:45.123456Z",
#       "type": "ds_etc",
#       "label": "Production Deployment Server",
#       "status": "stored",
#       "notes": "Weekly configuration backup"
#     }
#   ],
#   "total": 1,
#   "page": 1,
#   "per_page": 50
# }
```

**Get Run Details:**
```bash
# Get details for a specific run
curl http://localhost:8000/v1/runs/42

# Example response:
# {
#   "id": 42,
#   "created_at": "2025-01-15T10:30:45.123456Z",
#   "type": "ds_etc",
#   "label": "Production Deployment Server",
#   "status": "stored",
#   "notes": "Weekly configuration backup"
# }
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

### Database Readiness Strategy

The application implements a robust database readiness/wait strategy to prevent race conditions during startup in both local development and CI environments. This ensures the database is fully ready before the application starts or migrations run.

**Automatic Wait on Startup:**

When using Docker Compose, the API service automatically waits for the database to be ready before starting:

```bash
# Start all services - API will wait for database automatically
docker compose up -d

# Check logs to see the wait process
docker compose logs -f api
```

**Manual Database Wait:**

For local development or custom setups, you can manually wait for the database:

```bash
# Using Python script (recommended)
cd backend
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/splunk_auto_doc"
python scripts/wait_for_db.py

# Using shell script (requires PostgreSQL client tools)
cd backend
export DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_NAME=splunk_auto_doc
./scripts/wait-for-db.sh

# With custom retry settings
python scripts/wait_for_db.py --max-retries 60 --retry-interval 1
```

**Health Check Endpoints:**

The application provides health check endpoints that verify database connectivity:

```bash
# Basic health check (always returns 200)
curl http://localhost:8000/health/

# Readiness check (returns 200 if DB is ready, 503 if not)
curl http://localhost:8000/health/ready
curl http://localhost:8000/v1/ready
```

**CI/CD Integration:**

The CI workflow automatically waits for the database before running migrations and tests. See `.github/workflows/backend-ci.yml` for the implementation.

**Configuration Options:**

Environment variables control the wait behavior:
- `DB_MAX_RETRIES` - Maximum retry attempts (default: 30)
- `DB_RETRY_INTERVAL` - Seconds between retries (default: 2)
- `DATABASE_URL` - Full database connection string (required)

**Troubleshooting:**

If database connection fails:
1. Verify PostgreSQL container is running: `docker compose ps db`
2. Check database logs: `docker compose logs db`
3. Ensure health check passes: `docker compose ps` (should show "healthy")
4. Test connection manually: `psql $DATABASE_URL -c "SELECT 1;"`
5. Check environment variables in `.env` file

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

## Troubleshooting

### Common Setup Issues

**Docker Compose fails to start:**
```bash
# Check if ports are already in use
lsof -i :8000  # API port
lsof -i :3000  # Frontend port
lsof -i :5432  # PostgreSQL port
lsof -i :9000  # MinIO port

# Stop conflicting services or change ports in docker-compose.yml
docker compose down
docker compose up -d
```

**Database connection errors:**
```bash
# Ensure PostgreSQL container is healthy
docker compose ps

# Check database logs
docker compose logs db

# The API service automatically waits for database readiness
# If you need to manually wait for the database:
cd backend
python scripts/wait_for_db.py

# Test database connectivity
curl http://localhost:8000/health/ready

# If readiness check fails, check DATABASE_URL environment variable
docker compose exec api env | grep DATABASE_URL

# Restart services if database was not ready during initial startup
docker compose restart api
```

**MinIO/Storage errors:**
```bash
# Check MinIO is running
docker compose ps minio

# Verify storage configuration in .env
cat .env | grep STORAGE

# For local storage, ensure directory exists and has write permissions
mkdir -p ./data/uploads
chmod 755 ./data/uploads
```

**Frontend can't connect to API:**
```bash
# Verify API is running
curl http://localhost:8000/v1/health

# Check VITE_API_URL in frontend/.env
cat frontend/.env

# Ensure VITE_API_URL=http://localhost:8000 for local development
```

### Testing Issues

**Backend tests fail:**
```bash
# Install all dependencies including dev requirements
pip install -e ".[dev]"

# Clear pytest cache
rm -rf .pytest_cache
rm -rf backend/.pytest_cache

# Run with verbose output to see specific failures
pytest backend/tests/ -vv

# Run single test to isolate issue
pytest backend/tests/test_uploads.py::test_upload_success -vv
```

**Frontend tests fail:**
```bash
# Reinstall node_modules
cd frontend
rm -rf node_modules package-lock.json
npm install

# Clear Vitest cache
rm -rf node_modules/.vite

# Run with UI for interactive debugging
npm run test:ui
```

**Import errors in tests:**
```bash
# Ensure you're running from project root
cd /path/to/Splunk_auto_doc

# Backend: Install in editable mode
pip install -e .

# Frontend: Ensure proper module resolution
cd frontend && npm run build
```

### CI/CD Issues

**Pre-commit hooks fail:**
```bash
# Update pre-commit to latest version
pre-commit autoupdate

# Clear cache and reinstall
pre-commit clean
pre-commit install --install-hooks

# Run manually to debug
pre-commit run --all-files --verbose
```

**GitHub Actions CI fails:**

1. **Check the specific failure** - Click on the failed check in PR to see logs
2. **Reproduce locally** - Run the same commands from the CI workflow:
   ```bash
   # Backend CI steps
   ruff check backend/
   ruff format --check backend/
   mypy backend/app/
   pytest backend/tests/ --cov=backend/app

   # Frontend CI steps
   cd frontend
   npm run lint
   npm run format:check
   npm run build
   npm run test
   ```
3. **Fix the issue** - Address the specific error shown in logs
4. **Push again** - CI will automatically re-run

**Migration conflicts:**
```bash
# Check current migration state
cd backend
alembic current

# View migration history
alembic history

# If migrations are out of sync, downgrade and re-apply
alembic downgrade base
alembic upgrade head
```

### Performance Issues

**Slow uploads:**
```bash
# Check available disk space
df -h

# Monitor upload progress with verbose logging
LOG_LEVEL=DEBUG docker compose logs -f api

# For large files, ensure streaming is working (not loading into memory)
# Check memory usage: docker stats
```

**Database query performance:**
```bash
# Connect to database and check slow queries
docker compose exec db psql -U splunk_user -d splunk_auto_doc

# In psql:
# SELECT * FROM pg_stat_activity WHERE state = 'active';
# EXPLAIN ANALYZE SELECT * FROM ingestion_runs ORDER BY created_at DESC LIMIT 50;
```

### Getting Additional Help

- Check the [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Review [milestone plans](notes/milestone-1-plan.md) for project architecture
- Review [gap analysis](notes/milestone-1-gap-analysis.md) for known issues
- Check [database schema docs](notes/database-schema.md) for data model questions
- Open a GitHub issue with:
  - Description of the problem
  - Steps to reproduce
  - Error messages and logs
  - Your environment (OS, Docker version, Python version)

## Project Documentation

### Core Documentation Files

- **[README.md](README.md)** - This file, project overview and quick start
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines and development workflow
- **[TESTING.md](TESTING.md)** - Comprehensive testing documentation

### Planning & Architecture

- **[docs/adr/](docs/adr/)** - Architecture Decision Records (ADRs)
  - **[ADR-001: Core Stack Selection](docs/adr/ADR-001-core-stack.md)** - Technology stack rationale
- **[notes/milestone-1-plan.md](notes/milestone-1-plan.md)** - Milestone 1 objectives and scope
- **[notes/milestone-1-gap-analysis.md](notes/milestone-1-gap-analysis.md)** - Progress tracking and gaps
- **[notes/database-schema.md](notes/database-schema.md)** - Database schema documentation
- **[notes/logging-implementation.md](notes/logging-implementation.md)** - Logging system details
- **[notes/Project description.md](notes/Project%20description.md)** - Overall project vision and design
- **[notes/github-instructions.md](notes/github-instructions.md)** - Coding standards reference

---

**Current Status**: Milestone 1 - Project skeleton and upload ingestion foundation completed.

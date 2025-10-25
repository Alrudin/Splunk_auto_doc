# GitHub Copilot Instructions for Splunk Auto Doc

## Project Overview

Splunk Auto Doc is a web application that parses and analyzes Splunk configuration files to generate comprehensive documentation and visualizations. The tool helps Splunk administrators understand data flow, configuration dependencies, and routing paths within their Splunk deployments.

### Key Features
- Configuration parsing of Splunk .conf files (inputs.conf, props.conf, transforms.conf, etc.)
- Asynchronous background processing with Celery workers
- Full provenance tracking for all parsed configurations
- REST API for uploads, parsing status, and retrieval
- React-based web interface for file uploads and viewing ingestion runs

### Architecture
- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15+ with SQLAlchemy/SQLModel
- **Storage**: MinIO or local filesystem for blob storage
- **Queue**: Redis + Celery for async task processing
- **Deployment**: Docker Compose for development

## Technology Stack

### Backend
- **Python 3.11+** with type hints required
- **FastAPI** for REST API with automatic OpenAPI docs
- **Pydantic v2** for data validation and serialization
- **SQLAlchemy/SQLModel** for database ORM
- **PostgreSQL** as primary data store
- **Celery** for background task processing
- **Redis** for task queue
- **boto3** for S3-compatible object storage (MinIO)

### Frontend
- **React 18+** with functional components and hooks
- **TypeScript** with strict type checking
- **Vite** as build tool
- **TailwindCSS** for styling
- **Vitest** for testing
- **ESLint + Prettier** for code quality

## Project Structure

```
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── api/          # API route handlers
│   │   ├── core/         # Core configuration and utilities
│   │   ├── models/       # SQLAlchemy database models
│   │   ├── schemas/      # Pydantic schemas for request/response
│   │   ├── services/     # Business logic services
│   │   ├── storage/      # Storage abstraction layer
│   │   ├── parser/       # Configuration file parsing logic
│   │   ├── worker/       # Celery worker tasks
│   │   ├── health.py     # Health check endpoints
│   │   └── main.py       # FastAPI application entry point
│   ├── tests/            # Backend tests
│   ├── alembic/          # Database migrations
│   └── scripts/          # Utility scripts
├── frontend/             # React + TypeScript frontend
│   ├── src/
│   │   ├── api/          # API client functions
│   │   ├── pages/        # Page components
│   │   ├── layouts/      # Layout components
│   │   ├── types/        # TypeScript type definitions
│   │   └── test/         # Frontend tests
│   └── public/           # Static assets
├── notes/               # Project documentation and plans
└── docker-compose.yml   # Development environment setup
```

## Coding Standards

### Python Standards

**Core Principles:**
- Follow PEP 8 style guide strictly
- Always use type hints for function parameters and return values
- Write docstrings for all public functions and classes (Google-style)
- Use descriptive variable and function names
- Maintain 4-space indentation
- Line length max 88 characters (ruff default)

**Type Hints:**
```python
# ✅ Good: Complete type hints
def create_ingestion_run(
    file_path: str,
    upload_type: str,
    label: str | None = None
) -> IngestionRun:
    """Create a new ingestion run from an uploaded file.

    Args:
        file_path: Path to the uploaded file
        upload_type: Type of upload (ds_etc, instance_etc, etc.)
        label: Optional human-readable label

    Returns:
        IngestionRun: The created ingestion run

    Raises:
        ValueError: If upload_type is invalid
    """
    pass

# ❌ Bad: Missing type hints and docstring
def create(f, t, l=None):
    pass
```

**Async/Await Patterns:**
```python
# Database operations are synchronous
def get_run(db: Session, run_id: int) -> IngestionRun | None:
    return db.query(IngestionRun).filter(IngestionRun.id == run_id).first()

# API endpoints can be async
@router.get("/runs/{run_id}")
async def read_run(run_id: int, db: Session = Depends(get_db)) -> RunResponse:
    run = get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
```

**Error Handling:**
```python
# Use FastAPI HTTPException for API errors
from fastapi import HTTPException

if not run:
    raise HTTPException(status_code=404, detail="Run not found")

# Use custom exceptions for business logic
class ParsingError(Exception):
    """Raised when configuration parsing fails."""
    pass
```

### TypeScript/React Standards

**Core Principles:**
- Use TypeScript with strict mode enabled
- Avoid `any` type - use specific types or `unknown`
- Use functional components with hooks
- Use PascalCase for components, camelCase for functions/variables
- Maintain 2-space indentation
- Follow ESLint rules configured in project

**Component Structure:**
```typescript
// ✅ Good: Explicit types, clear interface
interface UploadFormProps {
  onUploadComplete: (runId: number) => void
  allowedTypes: string[]
}

export const UploadForm: React.FC<UploadFormProps> = ({
  onUploadComplete,
  allowedTypes,
}) => {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    setUploading(true)
    try {
      const runId = await uploadFile(file)
      onUploadComplete(runId)
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }

  return <form onSubmit={handleSubmit}>...</form>
}

// ❌ Bad: Any types, missing interfaces
export const UploadForm = ({ onUploadComplete, allowedTypes }: any) => {
  const [file, setFile] = useState(null)
  // Implementation
}
```

**API Client Patterns:**
```typescript
// Define response types
interface RunResponse {
  id: number
  status: 'pending' | 'running' | 'complete' | 'failed'
  created_at: string
}

// Type-safe API calls
export const fetchRun = async (runId: number): Promise<RunResponse> => {
  const response = await fetch(`${API_BASE_URL}/v1/runs/${runId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch run: ${response.statusText}`)
  }
  return response.json()
}
```

## Testing Requirements

### Backend Testing

**Framework:** pytest with pytest-asyncio, pytest-cov

**Test Organization:**
- Place tests in `backend/tests/`
- Name test files `test_*.py`
- Use fixtures from `conftest.py` for common setup
- Test both success and error cases
- Aim for 70%+ coverage, 80%+ for critical paths

**Test Patterns:**
```python
import pytest
from fastapi.testclient import TestClient

def test_create_run_success(client: TestClient, sample_upload_metadata: dict):
    """Test successful run creation."""
    response = client.post("/v1/runs", json=sample_upload_metadata)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"

def test_create_run_invalid_type(client: TestClient):
    """Test run creation with invalid upload type."""
    response = client.post("/v1/runs", json={"upload_type": "invalid"})
    assert response.status_code == 422

@pytest.mark.database
def test_database_query(db_session):
    """Test database operations directly."""
    # Use db_session fixture for raw database access
    pass
```

**Available Fixtures:**
- `client`: FastAPI TestClient with test database and storage
- `test_db`: In-memory SQLite database
- `test_storage`: Temporary directory storage
- `db_session`: Direct database session access
- `sample_tar_file`: Sample configuration archive
- `sample_upload_metadata`: Sample metadata for uploads

### Frontend Testing

**Framework:** Vitest with @testing-library/react

**Test Organization:**
- Place tests in `frontend/src/test/` or colocate as `*.test.tsx`
- Test components, hooks, and utility functions
- Focus on user interactions and edge cases

**Test Patterns:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { UploadForm } from '../pages/UploadForm'

describe('UploadForm', () => {
  it('calls onUploadComplete when upload succeeds', async () => {
    const mockOnComplete = vi.fn()
    render(<UploadForm onUploadComplete={mockOnComplete} allowedTypes={['.tar.gz']} />)

    const fileInput = screen.getByLabelText(/select file/i)
    const file = new File(['content'], 'test.tar.gz', { type: 'application/gzip' })

    fireEvent.change(fileInput, { target: { files: [file] } })
    fireEvent.click(screen.getByText(/upload/i))

    // Wait for async upload
    await screen.findByText(/upload complete/i)
    expect(mockOnComplete).toHaveBeenCalledWith(expect.any(Number))
  })
})
```

## Common Commands

### Development Setup
```bash
# Backend setup
pip install -e ".[dev]"
pre-commit install

# Frontend setup
cd frontend && npm install

# Start development environment
docker compose up -d
```

### Testing
```bash
# Backend tests
make test-backend
pytest backend/tests/ -v

# Frontend tests
make test-frontend
cd frontend && npm run test

# Coverage reports
make test-coverage
```

### Code Quality
```bash
# Backend linting
make lint
ruff check backend/

# Backend formatting
make format
ruff format backend/

# Backend type checking
make type-check
mypy backend/app/

# Frontend linting
cd frontend && npm run lint

# Frontend formatting
cd frontend && npm run format

# Run all pre-commit hooks
pre-commit run --all-files
```

### Database
```bash
# Wait for database to be ready
make wait-for-db

# Run migrations
make migrate
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"
```

## Database Patterns

### Models (SQLAlchemy/SQLModel)
```python
from sqlmodel import Field, SQLModel
from datetime import datetime

class IngestionRun(SQLModel, table=True):
    """Represents an ingestion run."""
    __tablename__ = "ingestion_runs"

    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(index=True)
    upload_type: str
    label: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Schemas (Pydantic)
```python
from pydantic import BaseModel, Field
from datetime import datetime

class RunCreate(BaseModel):
    """Schema for creating a new run."""
    upload_type: str = Field(..., description="Type of upload")
    label: str | None = Field(None, description="Optional label")

class RunResponse(BaseModel):
    """Schema for run response."""
    id: int
    status: str
    upload_type: str
    label: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

## Storage Patterns

The project uses an abstraction layer for storage that supports both local filesystem and S3-compatible object storage (MinIO).

```python
from app.storage import get_storage_backend

# Get storage backend (configured via environment)
storage = get_storage_backend()

# Upload file
file_hash = await storage.upload_file(
    file_content=file_bytes,
    filename="config.tar.gz",
    run_id=run.id
)

# Download file
file_content = await storage.download_file(file_hash)

# Delete file
await storage.delete_file(file_hash)
```

## Worker/Task Patterns

Background tasks are handled by Celery workers.

```python
from celery import shared_task
from app.worker.celery_app import celery_app

@shared_task(bind=True, max_retries=3)
def parse_run(self, run_id: int) -> dict:
    """Parse configuration files for an ingestion run.

    Args:
        run_id: ID of the ingestion run to parse

    Returns:
        dict: Parsing results with file and stanza counts

    Raises:
        Retry: If parsing fails and retries remain
    """
    try:
        # Parsing logic
        return {"files": 10, "stanzas": 100}
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

## Important Notes

1. **Database Readiness**: Always wait for database before running migrations or starting the API. Use `make wait-for-db` or the `wait_for_db.py` script.

2. **Provenance Tracking**: All parsed configurations must include full metadata (app, scope, layer, file, line numbers).

3. **Error Handling**: Use appropriate HTTP status codes (404 for not found, 422 for validation errors, 500 for server errors).

4. **Security**: Never commit secrets. Use environment variables. The project uses `.env` files (not committed).

5. **Migrations**: Always test migrations with both upgrade and downgrade. Use `alembic revision --autogenerate` for schema changes.

6. **API Versioning**: All endpoints are under `/v1/` prefix. Maintain backward compatibility.

## Additional Documentation

For more detailed information, refer to:
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Full contribution guidelines
- [TESTING.md](../TESTING.md) - Comprehensive testing documentation
- [README.md](../README.md) - Project overview and setup
- [notes/github-instructions.md](../notes/github-instructions.md) - Additional coding standards
- [notes/database-schema.md](../notes/database-schema.md) - Database design
- [notes/milestone-2-plan.md](../notes/milestone-2-plan.md) - Current milestone specifications

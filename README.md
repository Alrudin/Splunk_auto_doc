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
   - Frontend: http://localhost:3000 (placeholder with service status)
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

2. **Database setup**
   ```bash
   # Run database migrations
   cd backend
   alembic upgrade head
   
   # Check current migration version
   alembic current
   
   # View migration history
   alembic history
   ```

3. **Run tests**
   ```bash
   # Run all tests
   pytest backend/tests/
   
   # Run with coverage
   pytest backend/tests/ --cov=backend/app
   ```

4. **Code quality checks**
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

---

**Current Status**: Milestone 1 - Project skeleton and upload ingestion foundation in progress.
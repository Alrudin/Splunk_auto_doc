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
   # Run database migrations (future milestone)
   alembic upgrade head
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

# Upload Splunk configuration (future milestone)
curl -X POST "http://localhost:8000/v1/uploads" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@splunk_etc.tar.gz"

# List ingestion runs (future milestone)
curl http://localhost:8000/v1/runs
```

---

**Current Status**: Milestone 1 - Project skeleton and upload ingestion foundation in progress.
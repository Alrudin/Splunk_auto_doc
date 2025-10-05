# Testing Guide

This document provides comprehensive information about testing in the Splunk Auto Doc project.

## Overview

The project has two main test suites:
- **Backend Tests**: Python tests using pytest
- **Frontend Tests**: TypeScript/React tests using Vitest

Both test suites support unit tests, integration tests, and code coverage reporting.

## Quick Start

```bash
# Run all backend tests
make test-backend

# Run all frontend tests
make test-frontend

# Run tests with coverage
make test-coverage
```

## Backend Testing

### Technology Stack
- **pytest** - Test framework
- **pytest-cov** - Coverage plugin
- **pytest-asyncio** - Async test support
- **FastAPI TestClient** - API testing
- **SQLAlchemy** - Database testing with in-memory SQLite

### Test Organization

```
backend/tests/
├── __init__.py              # Package marker
├── conftest.py              # Shared pytest fixtures
├── test_basic.py            # Basic structure tests (no dependencies)
├── test_health.py           # Health endpoint tests
├── test_health_simulation.py # Health endpoint simulation tests
├── test_health_v1.py        # V1 health endpoint tests
├── test_models.py           # Database model tests
├── test_schemas.py          # Pydantic schema tests
├── test_storage.py          # Storage backend tests
├── test_uploads.py          # Upload endpoint integration tests
├── test_runs.py             # Runs endpoint integration tests
├── test_logging.py          # Logging configuration tests
├── test_api_endpoints.py    # API endpoint unit tests
└── test_error_handling.py   # Error handling integration tests
```

### Shared Fixtures (conftest.py)

The `conftest.py` file provides reusable test fixtures:

```python
@pytest.fixture
def test_db():
    """In-memory SQLite database for isolated testing."""
    # Creates a fresh database for each test

@pytest.fixture
def test_storage():
    """Temporary directory storage backend."""
    # Automatically cleaned up after test

@pytest.fixture
def client(test_db, test_storage):
    """FastAPI TestClient with test dependencies."""
    # Database and storage overrides applied

@pytest.fixture
def db_session(test_db):
    """Direct database session access."""
    # For tests that need raw DB access

@pytest.fixture
def sample_tar_file():
    """Sample file for upload tests."""

@pytest.fixture
def sample_upload_metadata():
    """Sample metadata for upload tests."""

@pytest.fixture
def large_file():
    """Large file (5MB) for performance testing."""

@pytest.fixture
def sample_files():
    """Multiple sample files for batch testing."""
```

### Upload Lifecycle Test Coverage

The test suite provides comprehensive coverage for the upload lifecycle:

**Unit Tests:**
- ✅ File upload validation (type, metadata)
- ✅ SHA256 hash computation
- ✅ File size tracking
- ✅ Metadata accuracy (label, notes, type)
- ✅ Empty file handling
- ✅ Invalid ingestion type validation
- ✅ Missing required fields validation
- ✅ Special characters in filenames

**Integration Tests:**
- ✅ End-to-end upload flow (upload → storage → database)
- ✅ Blob retrievability from storage
- ✅ Multiple sequential uploads
- ✅ Incremental ingestion scenarios
- ✅ Concurrent upload isolation
- ✅ Large file handling (1MB-10MB)

**Error Handling Tests:**
- ✅ Storage backend failures
- ✅ Database transaction failures
- ✅ Empty file uploads
- ✅ Invalid metadata
- ✅ Missing file field
- ✅ Multiple file uploads (unsupported)
- ✅ Very long labels and notes

**Storage Backend Tests:**
- ✅ Local storage operations
- ✅ Blob store/retrieve/delete
- ✅ Nested path handling
- ✅ Binary data integrity
- ✅ Large file storage
- ✅ Nonexistent blob handling

### Running Backend Tests

```bash
# All tests
pytest backend/tests/

# Specific test file
pytest backend/tests/test_uploads.py

# Specific test class
pytest backend/tests/test_uploads.py::TestUploadEndpoint

# Specific test method
pytest backend/tests/test_uploads.py::TestUploadEndpoint::test_upload_success

# With verbose output
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=backend/app

# With HTML coverage report
pytest backend/tests/ --cov=backend/app --cov-report=html

# Stop on first failure
pytest backend/tests/ -x

# Show print statements
pytest backend/tests/ -s
```

### Test Categories

#### Unit Tests
- `test_models.py` - Database model structure and validation
- `test_schemas.py` - Pydantic schema validation
- `test_api_endpoints.py` - Individual endpoint behavior

#### Integration Tests
- `test_uploads.py` - Full upload lifecycle (POST → storage → DB)
- `test_runs.py` - Runs listing and detail retrieval
- `test_storage.py` - Storage backend operations
- `test_error_handling.py` - Error scenarios across the stack

#### Smoke Tests
- `test_basic.py` - Basic structure without external dependencies
- `test_health_simulation.py` - Health endpoints without server

### Writing New Backend Tests

**Basic Test Example:**
```python
def test_my_feature(client):
    """Test my feature."""
    response = client.get("/v1/my-endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

**Database Test Example:**
```python
def test_database_operation(db_session):
    """Test database operation."""
    from app.models import MyModel

    obj = MyModel(name="test")
    db_session.add(obj)
    db_session.commit()

    result = db_session.query(MyModel).filter_by(name="test").first()
    assert result is not None
    assert result.name == "test"
```

**Upload Test Example:**
```python
def test_file_upload(client, sample_tar_file, sample_upload_metadata):
    """Test file upload."""
    response = client.post(
        "/v1/uploads",
        files={"file": ("test.tar.gz", sample_tar_file, "application/gzip")},
        data=sample_upload_metadata
    )
    assert response.status_code == 201
```

## Frontend Testing

### Technology Stack
- **Vitest** - Fast test framework (Vite-native)
- **React Testing Library** - Component testing utilities
- **@vitest/coverage-v8** - Coverage reporting
- **jsdom** - DOM implementation for Node.js

### Test Organization

```
frontend/src/test/
├── setup.ts              # Test setup and configuration
├── App.test.ts           # Basic application tests
├── HomePage.test.tsx     # HomePage component tests
├── MainLayout.test.tsx   # MainLayout component tests
├── ApiClient.test.ts     # API client wrapper tests
└── Navigation.test.tsx   # Routing integration tests
```

### Running Frontend Tests

```bash
# All tests
cd frontend && npm run test

# With UI (interactive mode)
cd frontend && npm run test:ui

# With coverage
cd frontend && npm run test:coverage

# Watch mode (re-run on changes)
cd frontend && npm run test -- --watch

# Specific test file
cd frontend && npm run test -- src/test/HomePage.test.tsx

# With verbose output
cd frontend && npm run test -- --reporter=verbose
```

### Test Categories

#### Unit Tests
- `HomePage.test.tsx` - HomePage component rendering and content
- `MainLayout.test.tsx` - Layout structure and navigation
- `ApiClient.test.ts` - HTTP client methods and error handling

#### Integration Tests
- `Navigation.test.tsx` - React Router integration
- `App.test.ts` - Full app component integration

### Writing New Frontend Tests

**Component Test Example:**
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

**API Client Test Example:**
```typescript
import { describe, it, expect, vi } from 'vitest'
import apiClient from '../api/client'

// Mock fetch
global.fetch = vi.fn()

describe('API Client', () => {
  it('should make GET request', async () => {
    const mockData = { id: 1 }
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    })

    const result = await apiClient.get('/endpoint')
    expect(result).toEqual(mockData)
  })
})
```

**User Interaction Test Example:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react'

it('should handle button click', () => {
  render(<MyComponent />)
  const button = screen.getByText('Click Me')
  fireEvent.click(button)
  expect(screen.getByText('Clicked!')).toBeDefined()
})
```

## Coverage Goals

### Minimum Coverage Targets
- **Overall**: 70% for touched/modified code
- **Critical Paths**: 80%+ (uploads, runs, storage, API endpoints)
- **New Features**: 80%+ for all new code

### Coverage Reports

**Backend:**
```bash
# Generate HTML report
pytest backend/tests/ --cov=backend/app --cov-report=html

# View report
open htmlcov/index.html
```

**Frontend:**
```bash
# Generate coverage report
cd frontend && npm run test:coverage

# View report
open frontend/coverage/index.html
```

### Coverage Configuration

**Backend** (`pyproject.toml`):
- Source: `backend/app`
- Omit: `backend/tests/*`, `backend/app/__init__.py`
- Excludes: `pragma: no cover`, abstract methods, debug code

**Frontend** (`vitest.config.ts`):
- Provider: v8
- Reporters: text, json, html
- Excludes: `node_modules/`, `src/test/`, `*.d.ts`, `*.config.*`, `dist/`

## Continuous Integration

Tests run automatically on:
- Every pull request
- Every commit to main branch
- Manual workflow dispatch

CI Workflow:
1. Checkout code
2. Install dependencies
3. Run linters
4. Run backend tests with coverage
5. Run frontend tests with coverage
6. Upload coverage reports
7. Check coverage thresholds

## Troubleshooting

### Backend Issues

**"Dependencies not available"**
- Install with: `pip install -e ".[dev]"`
- Verify: `pytest --version`

**Import errors**
- Ensure you're in project root
- Check `PYTHONPATH` includes backend directory

**Database errors**
- Tests use in-memory SQLite - no external DB needed
- Check that all models are imported in `conftest.py`

**Timeout issues**
- Increase pytest timeout: `pytest --timeout=300`
- Check for blocking operations in tests

### Frontend Issues

**"Module not found"**
- Install dependencies: `cd frontend && npm install`
- Verify: `npm list vitest`

**Component test failures**
- Ensure components wrapped in Router/Provider context
- Check for missing mock data

**Coverage missing**
- Install coverage package: `npm install --save-dev @vitest/coverage-v8`
- Check `vitest.config.ts` has coverage configuration

### Common Issues

**Port conflicts**
- No ports needed for tests (TestClient used instead of server)
- Check no dev servers running during tests

**File permission errors**
- Temporary directories created with proper permissions
- Check filesystem supports creation of temp files

**Memory issues**
- In-memory SQLite should be lightweight
- Consider running tests in smaller batches

## Best Practices

### General
- ✅ Write tests before fixing bugs (TDD for bug fixes)
- ✅ Test both success and failure cases
- ✅ Use descriptive test names that explain what is tested
- ✅ Keep tests focused - one concept per test
- ✅ Use fixtures/setup to reduce duplication
- ✅ Clean up resources after tests
- ❌ Don't test framework behavior (test your code)
- ❌ Don't couple tests to implementation details
- ❌ Don't use production databases in tests

### Backend
- Use `test_db` and `test_storage` fixtures
- Test endpoints through `client` fixture
- Verify database state after operations
- Check response status codes and structure
- Test edge cases (empty files, invalid data)

### Frontend
- Wrap components in required context providers
- Use `screen.getByText` and semantic queries
- Test user interactions, not implementation
- Mock external API calls
- Test error states and loading states

## Examples

See existing tests for comprehensive examples:
- Backend: `backend/tests/test_uploads.py`
- Frontend: `frontend/src/test/HomePage.test.tsx`

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

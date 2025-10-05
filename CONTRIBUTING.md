# Contributing to Splunk Auto Doc

Thank you for your interest in contributing to Splunk Auto Doc! This document provides guidelines and information for contributors.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alrudin/Splunk_auto_doc.git
   cd Splunk_auto_doc
   ```

2. **Set up the development environment**
   ```bash
   # Install backend dependencies
   pip install -e ".[dev]"

   # Install frontend dependencies
   cd frontend
   npm install
   cd ..

   # Set up pre-commit hooks
   pre-commit install
   ```

3. **Run tests to verify setup**
   ```bash
   # Backend tests
   pytest backend/tests/

   # Frontend tests
   cd frontend
   npm run test
   ```

4. **Understanding Database Readiness**

   The project implements a robust database readiness strategy to prevent race conditions. When developing locally or in CI:

   **Docker Compose (Automatic):**
   ```bash
   # Database readiness is handled automatically
   docker compose up -d

   # The API waits for the database before starting
   docker compose logs -f api
   ```

   **Local Development (Manual):**
   ```bash
   # If running services separately, ensure database is ready first
   make wait-for-db

   # Or use the Python script directly
   cd backend
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/splunk_auto_doc"
   python scripts/wait_for_db.py

   # Then run migrations
   alembic upgrade head

   # Finally start the API
   python -m app.main
   ```

   **Readiness Checks:**
   ```bash
   # Check if the API and database are ready
   curl http://localhost:8000/health/ready

   # Returns 200 OK if ready, 503 Service Unavailable if not
   ```

   See the [Database Readiness Strategy](README.md#database-readiness-strategy) section in the README for complete documentation.

## Coding Standards

This project follows strict coding standards to ensure consistency and maintainability. Please refer to [`notes/github-instructions.md`](notes/github-instructions.md) for detailed coding standards.

### Python Code Standards

**Core Principles:**
- **Follow PEP 8**: Use the official Python style guide
- **Type Hints**: Always include type hints for function parameters and return values
- **Documentation**: Write clear docstrings for all functions and classes
- **Naming**: Use descriptive names for variables, functions, and classes
- **Indentation**: Use 4 spaces for each level of indentation
- **Testing**: Create tests for all new code

**Required Practices:**
```python
# ✅ Good: Type hints, docstring, descriptive names
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
    # Implementation
    pass

# ❌ Bad: No types, no docstring, unclear names
def create(f, t, l=None):
    # Implementation
    pass
```

**Documentation Requirements:**
- All public functions and classes must have docstrings
- Use Google-style docstrings (Args, Returns, Raises)
- Include examples for complex functions
- Keep comments up-to-date with code changes

### TypeScript/React Code Standards

**Core Principles:**
- **Follow ESLint rules**: The project uses TypeScript ESLint with React plugins
- **Type Safety**: Always use TypeScript types, avoid `any` when possible
- **Component Structure**: Use functional components with hooks
- **Naming**: Use PascalCase for components, camelCase for functions/variables
- **Indentation**: Use 2 spaces for each level of indentation
- **Testing**: Write unit tests for components and utilities

**Required Practices:**
```typescript
// ✅ Good: Explicit types, clear interface, proper naming
interface UploadFormProps {
  onUploadComplete: (runId: number) => void
  allowedTypes: string[]
}

export const UploadForm: React.FC<UploadFormProps> = ({
  onUploadComplete,
  allowedTypes,
}) => {
  const [file, setFile] = useState<File | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // Implementation
  }

  return <form onSubmit={handleSubmit}>...</form>
}

// ❌ Bad: Any types, unclear interface, missing types
export const UploadForm = ({ onUploadComplete, allowedTypes }: any) => {
  const [file, setFile] = useState(null)
  // Implementation
}
```

**Component Organization:**
- One component per file
- Co-locate tests with components or in `test/` directory
- Extract reusable logic into custom hooks
- Use TypeScript interfaces for props and state

### Code Quality Tools

We use several tools to maintain code quality:

**Backend (Python):**
- **Ruff**: For linting and code formatting
- **mypy**: For static type checking
- **pytest**: For testing
- **pre-commit**: For automated code quality checks

**Frontend (TypeScript/React):**
- **ESLint**: For linting
- **Prettier**: For code formatting
- **Vitest**: For testing
- **TypeScript**: For type checking

### Running Quality Checks

**Backend:**
```bash
# Format code
make format
# or: ruff format backend/

# Run linter
make lint
# or: ruff check backend/

# Type checking
make type-check
# or: mypy backend/app/

# Run all tests
make test
# or: pytest backend/tests/
```

**Frontend:**
```bash
cd frontend

# Run linter
npm run lint

# Format code
npm run format

# Check formatting (CI mode)
npm run format:check

# Run tests
npm run test

# Type checking (via build)
npm run build
```

**Pre-commit hooks:**
```bash
# Run all hooks on all files
pre-commit run --all-files

# Run hooks on staged files (automatic on commit)
pre-commit run
```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the coding standards
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   # Backend
   pytest backend/tests/
   ruff check backend/
   mypy backend/app/

   # Frontend
   cd frontend
   npm run lint
   npm run test
   cd ..

   # Or use pre-commit to run all checks
   pre-commit run --all-files
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

   Then open a pull request on GitHub. The CI workflows will automatically run to validate your changes.

## Continuous Integration

All pull requests must pass CI checks before they can be merged. The CI pipeline runs automatically on every push and pull request.

### CI Workflows

**Backend CI** [![Backend CI](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/backend-ci.yml)
- Runs on Python 3.11 and 3.12
- Includes PostgreSQL service with health checks
- Automatically waits for database readiness before running migrations/tests
- Checks: Wait for DB → Run migrations → Ruff linting → Ruff format → mypy type checking → pytest with coverage
- All steps must pass for the PR to be approved

**Frontend CI** [![Frontend CI](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/Alrudin/Splunk_auto_doc/actions/workflows/frontend-ci.yml)
- Runs on Node.js 20
- Checks: ESLint → Prettier format → TypeScript build → Vitest with coverage
- All steps must pass for the PR to be approved

### What to Do If CI Fails

If your PR fails CI checks:

1. **Check the CI logs** - Click on the failed check to see detailed error messages
2. **Run checks locally** - Use the commands from step 3 of the Development Workflow above
3. **Fix the issues** - Address linting, formatting, type errors, or test failures
4. **Commit and push** - The CI will automatically re-run on new commits

**Pro tip**: Run `pre-commit run --all-files` before pushing to catch most issues locally.

### Coverage Requirements

- Minimum 70% coverage for touched/modified code
- Critical paths (uploads, runs, storage) should have >80% coverage
- Coverage reports are automatically generated and can be viewed in CI logs

## Project Structure

```
├── backend/           # Python FastAPI backend
│   ├── app/          # Main application code
│   │   ├── routes/   # API route handlers
│   │   ├── services/ # Business logic services
│   │   └── storage/  # Storage abstractions
│   └── tests/        # Backend tests
├── frontend/         # React + Vite + TypeScript frontend
│   ├── src/          # Frontend source code
│   │   ├── api/      # API client functions
│   │   ├── pages/    # Page components
│   │   ├── layouts/  # Layout components
│   │   ├── types/    # TypeScript type definitions
│   │   └── test/     # Frontend tests
│   └── public/       # Static assets
├── notes/           # Project documentation and plans
└── docker-compose.yml  # Development environment
```

## Testing Guidelines

For detailed information about testing, see [TESTING.md](TESTING.md).

- Write unit tests for all new functions and classes
- Include integration tests for API endpoints
- Ensure tests are isolated and can run independently
- Use descriptive test names that explain what is being tested
- Aim for good test coverage but focus on testing important functionality
- All new code should have at least 70% test coverage
- Critical paths (uploads, runs, storage) should have 80%+ coverage

**Backend Testing (pytest):**
- Place tests in `backend/tests/`
- Name test files `test_*.py`
- Use fixtures from `conftest.py` for common test data
- Test both success and error cases
- See `backend/tests/test_uploads.py` for integration test examples
- See `backend/tests/test_api_endpoints.py` for unit test examples

**Frontend Testing (Vitest):**
- Place tests in `frontend/src/test/` or alongside components as `*.test.ts(x)`
- Use Vitest for unit tests
- Use @testing-library/react for component testing
- Test user interactions and edge cases
- See `frontend/src/test/HomePage.test.tsx` for component test examples
- See `frontend/src/test/ApiClient.test.ts` for API client test examples

**Running Tests:**
```bash
# Run all backend tests
make test-backend

# Run all frontend tests
make test-frontend

# Run tests with coverage
make test-coverage
```

## Commit Message Guidelines

Use clear and descriptive commit messages:

```
type: Brief description of changes

Longer description if needed, explaining:
- What was changed and why
- Any breaking changes
- References to issues or PRs
```

Types:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring without functional changes
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

## Getting Help

- Check the [README.md](README.md) for setup instructions
- Review the [Architecture Decision Records](docs/adr/) for technology choices and rationale
- Review the [milestone plans](notes/milestone-1-plan.md) for project direction
- Review the [gap analysis](notes/milestone-1-gap-analysis.md) for current status
- Check the [database schema](notes/database-schema.md) for data model questions
- Open an issue for bugs or feature requests
- Ask questions in pull request discussions

## Submitting Issues

When opening an issue, please:

**For Bug Reports:**
1. Use the bug report template if available
2. Provide a clear, descriptive title
3. Include steps to reproduce the issue
4. Describe expected vs. actual behavior
5. Include relevant logs, screenshots, or error messages
6. Specify your environment (OS, Docker version, Python/Node version)

**For Feature Requests:**
1. Use the feature request template if available
2. Clearly describe the proposed feature
3. Explain the use case and benefits
4. Consider potential implementation approaches
5. Check if similar features are already planned in milestone docs

**For Documentation Issues:**
1. Identify which document needs updating
2. Describe what's unclear or missing
3. Suggest improvements if possible

## Submitting Pull Requests

**Before Submitting:**
1. Check that your branch is up-to-date with `main`
2. Run all quality checks locally: `pre-commit run --all-files`
3. Ensure all tests pass: `make test`
4. Update documentation if your changes affect usage or APIs
5. Add tests for new functionality

**PR Guidelines:**
1. **Create a descriptive title** - Use conventional commit format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `refactor:` for code refactoring
   - `test:` for test additions/changes
   - `chore:` for maintenance tasks

2. **Write a clear description**:
   - Explain what changes were made and why
   - Reference any related issues (e.g., "Fixes #123")
   - Describe testing performed
   - Note any breaking changes
   - Include screenshots for UI changes

3. **Keep PRs focused**:
   - One logical change per PR
   - Avoid mixing refactoring with new features
   - Split large changes into smaller, reviewable PRs

4. **Respond to feedback**:
   - Address reviewer comments promptly
   - Ask for clarification if feedback is unclear
   - Mark conversations as resolved after addressing them

**Example PR Description:**
```markdown
## Summary
Adds pagination support to the runs listing endpoint.

## Changes
- Added `page` and `per_page` query parameters to GET /v1/runs
- Updated response schema to include pagination metadata
- Added tests for pagination edge cases
- Updated API documentation with pagination examples

## Testing
- All existing tests pass
- Added new tests for:
  - Default pagination values
  - Custom page sizes
  - Out of range page numbers
  - Empty result sets

## Related Issues
Closes #42

## Screenshots
N/A (backend only)
```

## Code Review Process

All contributions must go through code review:

1. Create a pull request with a clear description
2. Ensure all CI checks pass
3. Address reviewer feedback promptly
4. Keep commits focused and well-organized

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

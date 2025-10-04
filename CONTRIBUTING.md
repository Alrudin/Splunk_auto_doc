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

## Coding Standards

This project follows strict coding standards to ensure consistency and maintainability. Please refer to [`notes/github-instructions.md`](notes/github-instructions.md) for detailed coding standards.

### Python Code Standards

- **Follow PEP 8**: Use the official Python style guide
- **Type Hints**: Always include type hints for function parameters and return values
- **Documentation**: Write clear docstrings for all functions and classes
- **Naming**: Use descriptive names for variables, functions, and classes
- **Indentation**: Use 4 spaces for each level of indentation
- **Testing**: Create tests for all new code

### TypeScript/React Code Standards

- **Follow ESLint rules**: The project uses TypeScript ESLint with React plugins
- **Type Safety**: Always use TypeScript types, avoid `any` when possible
- **Component Structure**: Use functional components with hooks
- **Naming**: Use PascalCase for components, camelCase for functions/variables
- **Indentation**: Use 2 spaces for each level of indentation
- **Testing**: Write unit tests for components and utilities

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
- Review the [milestone plans](notes/milestone-1-plan.md) for project direction
- Open an issue for bugs or feature requests
- Ask questions in pull request discussions

## Code Review Process

All contributions must go through code review:

1. Create a pull request with a clear description
2. Ensure all CI checks pass
3. Address reviewer feedback promptly
4. Keep commits focused and well-organized

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

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
   # Install dependencies
   make install
   
   # Set up pre-commit hooks
   make dev
   ```

3. **Run tests to verify setup**
   ```bash
   make test
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

### Code Quality Tools

We use several tools to maintain code quality:

- **Ruff**: For linting and code formatting
- **mypy**: For static type checking
- **pytest**: For testing
- **pre-commit**: For automated code quality checks

### Running Quality Checks

```bash
# Format code
make format

# Run linter
make lint

# Type checking
make type-check

# Run all tests
make test
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
   make test lint type-check
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
├── frontend/         # React frontend (future)
├── notes/           # Project documentation and plans
└── docker-compose.yml  # Development environment
```

## Testing Guidelines

- Write unit tests for all new functions and classes
- Include integration tests for API endpoints
- Ensure tests are isolated and can run independently
- Use descriptive test names that explain what is being tested
- Aim for good test coverage but focus on testing important functionality

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
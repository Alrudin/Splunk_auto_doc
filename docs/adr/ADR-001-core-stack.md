# ADR-001: Core Technology Stack Selection

**Status:** Accepted  
**Date:** 2025-01-XX  
**Decision Makers:** @Alrudin, Development Team  
**Related Documents:**
- [Milestone 1 Plan](../../notes/milestone-1-plan.md)
- [Milestone 1 Gap Analysis](../../notes/milestone-1-gap-analysis.md)
- [Project Description](../../notes/Project%20description.md)

---

## Context and Problem Statement

The Splunk Auto Doc project requires a robust, maintainable, and scalable technology stack to support configuration file parsing, analysis, and visualization. The initial architecture must establish patterns for:

1. **Backend API development** - REST endpoints for upload, metadata management, and future parsing operations
2. **Data persistence** - Relational data storage with strong schema guarantees and migration support
3. **Object storage** - Blob storage for uploaded configuration archives
4. **Frontend development** - Interactive web UI for uploading files and exploring results
5. **Development workflow** - Containerization, testing, and CI/CD automation
6. **Code quality** - Type safety, linting, formatting, and maintainability patterns

This decision establishes the foundational technology choices for Milestone 1 and beyond.

---

## Decision Drivers

### Technical Requirements
- **Type safety**: Strong typing to catch errors early and improve maintainability
- **Developer experience**: Fast iteration cycles, hot reload, comprehensive tooling
- **Scalability**: Ability to handle large configuration files (10k+ stanzas)
- **Testing**: First-class testing support with fixtures and mocking
- **API documentation**: Auto-generated API docs for backend endpoints
- **Production readiness**: Battle-tested technologies with strong ecosystem support

### Operational Requirements
- **Containerization**: Easy local development and deployment
- **Database migrations**: Safe, versioned schema evolution
- **Observability**: Structured logging, health checks, request tracing
- **Performance**: Efficient handling of file uploads and database queries

### Project Constraints
- **Timeline**: Milestone 1 foundation needed within 2 weeks
- **Team expertise**: Python and JavaScript/TypeScript familiarity
- **Open source**: Preference for well-maintained open source technologies
- **Community**: Active communities for troubleshooting and best practices

---

## Considered Options

### Backend Framework
1. **FastAPI** (Python) - Modern, async, auto-docs, type hints
2. **Django REST Framework** - Mature, batteries included, ORM
3. **Flask** - Lightweight, flexible, minimal
4. **Express.js** (Node.js) - JavaScript ecosystem, async by default

### Database
1. **PostgreSQL** - Relational, mature, JSON support, strong typing
2. **SQLite** - Simple, file-based, no server
3. **MongoDB** - Document store, flexible schema
4. **MySQL** - Relational, widely deployed

### Object Storage
1. **MinIO** - S3-compatible, self-hosted, local development friendly
2. **Local filesystem** - Simple, no dependencies
3. **AWS S3** - Managed, scalable, requires cloud account
4. **Azure Blob Storage** - Managed, requires cloud account

### Frontend Framework
1. **React** - Component-based, large ecosystem, TypeScript support
2. **Vue.js** - Progressive, simpler learning curve
3. **Svelte** - Compiled, minimal runtime
4. **Angular** - Full framework, opinionated

### Build Tools
1. **Vite** - Fast, modern, ESM-native
2. **Webpack** - Mature, highly configurable
3. **Parcel** - Zero-config bundler
4. **esbuild** - Extremely fast, Go-based

---

## Decision Outcome

### Chosen Stack

#### Backend: FastAPI + Python 3.11+
**Rationale:**
- **Automatic API documentation** via OpenAPI/Swagger reduces manual documentation burden
- **Pydantic v2** provides best-in-class runtime validation and serialization with type safety
- **Async support** enables efficient handling of I/O-bound operations (file uploads, database queries)
- **Type hints** improve IDE support, catch errors early, and serve as inline documentation
- **Active ecosystem** with excellent third-party libraries for parsing, validation, and testing
- **Performance** comparable to Node.js while maintaining Python's expressiveness
- **Team familiarity** with Python ecosystem for parsing and data processing

**Key Libraries:**
- **Pydantic v2**: Request/response schemas with runtime validation
- **SQLAlchemy/SQLModel**: ORM and query builder with type safety
- **python-multipart**: Multipart form data handling for file uploads
- **boto3/minio-py**: S3-compatible client for object storage

**Alternatives Rejected:**
- *Django REST Framework*: Too heavyweight for our use case; ORM less flexible than SQLAlchemy
- *Flask*: Lacks built-in async support and automatic API documentation
- *Express.js*: Would split team between Python (parsing) and JavaScript (API)

#### Database: PostgreSQL 15+
**Rationale:**
- **Relational model** fits normalized configuration data structure (runs, files, stanzas)
- **Strong typing** with schema enforcement prevents data corruption
- **JSONB support** for flexible metadata storage when needed
- **Migration tools** (Alembic) provide safe schema evolution
- **Performance** excellent for both OLTP and analytical queries
- **Mature ecosystem** with extensive tooling and monitoring support
- **Free and open source** with permissive license

**Migration Management:**
- **Alembic**: Industry-standard migration tool for SQLAlchemy
- Versioned schema changes tracked in version control
- Supports forward and backward migrations (when feasible)

**Alternatives Rejected:**
- *SQLite*: Insufficient for multi-user scenarios, limited concurrency
- *MongoDB*: Lack of schema enforcement risky for critical metadata; parsing rules benefit from relational model
- *MySQL*: PostgreSQL's JSON support and extensibility superior for our use case

#### Object Storage: MinIO (S3-Compatible)
**Rationale:**
- **S3-compatible API** enables seamless migration to AWS/cloud providers if needed
- **Self-hosted** simplifies local development (no cloud accounts required)
- **Docker-friendly** integrates cleanly with Docker Compose development environment
- **Separation of concerns** keeps large blobs out of database, improving performance
- **Scalability** supports future distributed storage needs

**Abstraction Layer:**
- Storage interface abstracts MinIO vs local filesystem
- Enables testing with local filesystem, production with MinIO or S3
- Interface: `store_blob(data, key) -> url`, `retrieve_blob(key) -> data`

**Alternatives Rejected:**
- *Local filesystem only*: Lacks cloud-readiness, harder to scale
- *Cloud-only (S3/Azure)*: Requires cloud accounts for development, increased complexity

#### Frontend: React 18 + Vite + TypeScript
**Rationale:**
- **React 18**: Industry-standard component framework with massive ecosystem
- **Vite**: Lightning-fast HMR (Hot Module Replacement) for rapid iteration
- **TypeScript**: Type safety catches errors at compile time, improves refactoring safety
- **Component model** matches our UI needs (upload forms, data tables, graphs)
- **React Query**: Excellent server state management with caching and invalidation
- **Large ecosystem**: Extensive libraries for visualization (d3, Cytoscape), UI components, routing

**Key Libraries:**
- **React Router**: Client-side routing for SPA navigation
- **React Query**: Server state caching and synchronization
- **TailwindCSS**: Utility-first CSS for rapid UI development
- **Vite**: Build tool and dev server with instant HMR
- **d3.js/Cytoscape.js**: Data visualization and graph rendering (future milestones)

**Alternatives Rejected:**
- *Vue.js*: Smaller ecosystem for enterprise tooling, team less familiar
- *Svelte*: Less mature ecosystem, fewer visualization libraries
- *Angular*: Too opinionated and heavyweight for our needs
- *Webpack*: Slower build times than Vite, more complex configuration

#### CSS Framework: TailwindCSS
**Rationale:**
- **Utility-first** approach enables rapid prototyping
- **No context switching** between HTML and CSS files
- **Design system** built-in via configuration
- **Production optimization** removes unused CSS automatically
- **Responsive design** utilities simplify mobile support

**Alternatives Rejected:**
- *Bootstrap*: Less flexible, harder to customize
- *Material-UI*: Opinionated design system, heavier bundle size
- *Plain CSS/SCSS*: More boilerplate, harder to maintain consistency

#### Containerization: Docker Compose
**Rationale:**
- **Local development parity** with production environment
- **Multi-service orchestration** (API, DB, MinIO, frontend, Redis) in single command
- **Environment isolation** prevents "works on my machine" issues
- **Onboarding simplicity**: New developers can start with `docker compose up`
- **Service health checks** ensure proper startup ordering

**Service Definitions:**
- `api`: FastAPI backend with hot reload
- `db`: PostgreSQL 15 with persistent volume
- `minio`: Object storage with console UI
- `redis`: Future task queue backend (placeholder in M1)
- `frontend`: Vite dev server with HMR

**Alternatives Rejected:**
- *Kubernetes*: Overkill for local development, too complex
- *Manual setup*: Error-prone, inconsistent across developers

#### Background Jobs: Celery + Redis (Future)
**Rationale (for future milestones):**
- **Asynchronous parsing**: Configuration parsing can take minutes for large archives
- **Task queue** enables progress tracking and cancellation
- **Retry logic** handles transient failures
- **Celery**: Industry-standard Python task queue with extensive monitoring tools
- **Redis**: Fast, simple, well-supported by Celery

**Note:** Not implemented in Milestone 1; parsing is synchronous for simplicity

---

## Key Architectural Patterns

### Service Layer Pattern
- **Routes** (API endpoints) → **Services** (business logic) → **Models** (data access)
- Separates HTTP concerns from domain logic
- Improves testability (can test services without HTTP layer)
- Example: `uploads.py` route calls `upload_service.create_ingestion_run()`

### Typed Schemas
- **Pydantic models** for all API requests and responses
- **SQLAlchemy models** for database entities
- Clear separation between ORM models and API schemas
- Prevents accidental exposure of internal fields

### Storage Abstraction
- **Interface**: `StorageBackend` with `store()`, `retrieve()`, `delete()` methods
- **Implementations**: `LocalStorageBackend`, `S3StorageBackend`
- Configuration-driven selection via environment variables
- Testability: Can mock storage backend in tests

### Structured Logging
- **JSON format** for machine-parseable logs in production
- **Text format** for human-readable logs in development
- **Correlation IDs** for request tracing across services
- **Contextual fields**: request_id, method, path, status_code, duration
- Compatible with log aggregators (Splunk, ELK, CloudWatch)

### Database Migrations
- **Alembic** for schema versioning
- Migrations tracked in `backend/alembic/versions/`
- Auto-generation from SQLAlchemy models: `alembic revision --autogenerate`
- Review all auto-generated migrations before applying

### Testing Strategy
- **Backend**: pytest with fixtures for database, storage, and HTTP client
- **Frontend**: Vitest + React Testing Library for components and integration
- **Coverage goals**: 70% minimum, 80%+ for critical paths (uploads, storage)
- **Integration tests**: End-to-end upload lifecycle validation
- **Test isolation**: In-memory SQLite for backend, MSW for frontend API mocking

### CI/CD Pipeline
- **GitHub Actions** for automated checks on every PR
- **Backend CI**: Ruff (lint) → mypy (types) → pytest (tests)
- **Frontend CI**: ESLint → TypeScript check → Vitest
- **Gating**: All checks must pass before merge
- **Caching**: Dependencies cached to speed up builds

---

## Quality Standards

### Code Quality Tools

**Backend:**
- **Ruff**: All-in-one linter and formatter (replaces black, isort, flake8)
- **mypy**: Static type checking with strict mode
- **pytest**: Testing with coverage tracking
- **pre-commit**: Automated checks before commit

**Frontend:**
- **ESLint**: JavaScript/TypeScript linting with React plugin
- **Prettier**: Code formatting
- **TypeScript**: Strict type checking
- **Vitest**: Fast unit test runner
- **pre-commit**: Automated checks before commit

### Type Safety
- **Backend**: All functions have type hints (PEP 484)
- **Frontend**: TypeScript strict mode enabled
- **API contracts**: Pydantic models ensure runtime type validation
- **Database**: SQLAlchemy models with type annotations

### Documentation Requirements
- **API docs**: Auto-generated via FastAPI/OpenAPI
- **Code comments**: Docstrings for all public functions (Google style)
- **Architecture**: This ADR and milestone plans
- **Database**: Schema documented in `notes/database-schema.md`
- **README**: Setup, quick start, troubleshooting

---

## Observability and Operations

### Logging
- **Structured logs**: JSON format in production
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Context injection**: Automatic request_id, user_id (future), timestamps
- **Middleware**: Request/response logging with duration tracking

### Health Checks
- **Endpoint**: `GET /health`
- **Checks**: Database connectivity, storage backend availability
- **Format**: `{"status": "ok", "checks": {"db": "ok", "storage": "ok"}}`
- **Docker**: Health check configuration in Compose for startup ordering

### Metrics (Future)
- Prometheus-compatible metrics endpoint
- Request duration histograms
- Upload size distribution
- Database query performance

---

## Consequences

### Positive
- **Rapid development**: Modern tooling enables fast iteration
- **Type safety**: Catches errors early, improves refactoring confidence
- **Scalability**: Architecture supports future growth (parsing, visualization, multi-tenancy)
- **Developer experience**: Hot reload, auto-docs, comprehensive testing
- **Production readiness**: Battle-tested technologies with strong support
- **Consistency**: Clear patterns for services, schemas, storage, logging
- **Testability**: Abstraction layers and dependency injection enable thorough testing

### Negative
- **Learning curve**: Developers new to FastAPI, React, or TypeScript need ramp-up time
- **Dependency management**: Multiple ecosystems (Python, Node.js) require separate tooling
- **Container overhead**: Docker adds complexity for developers unfamiliar with containers
- **Type annotations**: Requires discipline to maintain (especially in Python)

### Mitigations
- **Documentation**: Comprehensive README, CONTRIBUTING guide, and this ADR
- **Pre-commit hooks**: Automated enforcement of code quality standards
- **Examples**: Reference implementations for common patterns
- **Onboarding**: `docker compose up` gets new developers running quickly
- **CI enforcement**: Automated checks prevent quality regressions

---

## Trade-offs and Future Considerations

### Performance vs Simplicity
- **Current**: Synchronous parsing (Milestone 1 simplicity)
- **Future**: Celery background jobs for large archives (Milestone 2+)

### Storage Flexibility
- **Current**: MinIO for local development, abstracted for S3 compatibility
- **Future**: Can migrate to AWS S3, Azure Blob, or GCS without code changes

### Frontend State Management
- **Current**: React Query for server state
- **Future**: May add Zustand or Redux for complex client-side state (graph interactions)

### Authentication
- **Current**: None (Milestone 1 focus on core functionality)
- **Future**: OAuth2/OIDC integration (Milestone 7)

### Multi-tenancy
- **Current**: Single-tenant (no user isolation)
- **Future**: Add workspace/project scoping (Milestone 7)

---

## References

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [TailwindCSS Documentation](https://tailwindcss.com/)
- [MinIO Documentation](https://min.io/docs/)

### Internal Documentation
- [Milestone 1 Plan](../../notes/milestone-1-plan.md) - Detailed M1 scope and deliverables
- [Milestone 1 Gap Analysis](../../notes/milestone-1-gap-analysis.md) - Implementation progress tracking
- [Project Description](../../notes/Project%20description.md) - Overall vision and system design
- [Database Schema](../../notes/database-schema.md) - Data model documentation
- [Logging Implementation](../../notes/logging-implementation.md) - Structured logging details

### Architecture Decision Records
- This is ADR-001 (Core Stack Selection)
- Future ADRs will cover: parsing strategy, resolution algorithms, visualization approach, security model

---

## Decision History

| Date | Action | Notes |
|------|--------|-------|
| 2025-09-28 | Initial draft | Core stack decisions documented retrospectively for Milestone 1 |
| 2025-10-04 | Milestone 1 complete | All foundational components implemented and tested |
| 2025-01-XX | Formalized ADR | This document created to address gap identified in M1 analysis |

---

**Supersedes:** None (initial ADR)  
**Superseded by:** None (active)  
**Last Reviewed:** 2025-01-XX

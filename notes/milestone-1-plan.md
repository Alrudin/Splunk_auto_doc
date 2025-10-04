# Milestone 1 Plan – Project Skeleton & Upload Ingestion Foundation

Milestone Code: M1
Focus Window: Weeks 1–2 (adjust as needed)
Primary Goal: Stand up a reliable, testable baseline platform that can accept an upload, persist an ingestion run record, store the raw archive, and surface the run + basic statistics in a minimal UI. This creates the substrate for later parsing, normalization, and resolution logic.

---

## 1. Objectives

1. Provide a containerized development environment (API, DB, object storage, optional worker, frontend).
2. Implement initial FastAPI service with:
   - `POST /uploads` (accept tar/zip + metadata).
   - `GET /runs` (list basic metadata) & `GET /runs/:id`.
3. Persist `ingestion_runs` and `files` (archive entry only in M1; extracted file catalog optional/stub).
4. Store raw upload blobs in object storage (local disk or MinIO).
5. Frontend React skeleton with:
   - Upload page (drag & drop, select type, submit).
   - Run list/status page (polling or manual refresh).
6. Establish coding standards (PEP 8, type hints, tests required) and project scaffolding.
7. Implement logging, configuration management, and basic health endpoint.
8. CI pipeline: lint, type-check, run tests.
9. Documentation of architecture decisions relevant to M1 (ADR-001 style if desired).

Out of Scope for M1 (deferred to later milestones):
- Actual `.conf` parsing & stanza normalization.
- Serverclass membership or host/app resolution.
- Data path computation.
- Auth / RBAC.
- Graph visualization or diff views.
- Background job queue (can be stubbed synchronously).

---

## 2. Deliverables

| Category | Deliverable |
|----------|-------------|
| Infrastructure | `docker-compose.yml` running: api, db (PostgreSQL), minio (or local volume), (optional) redis placeholder, frontend |
| Backend | FastAPI app with modular layout (`app/`), config loader, logging setup, pydantic settings |
| Endpoints | `POST /v1/uploads`, `GET /v1/runs`, `GET /v1/runs/{id}`, `GET /health` |
| Persistence | Alembic (or equivalent) migrations for `ingestion_runs` and `files` tables |
| Storage | Blob persistence (filesystem or MinIO via S3 client), retrieval link/id |
| Frontend | React + Vite + Tailwind baseline, Upload form, Run list/status page |
| Testing | Unit tests (models, services, endpoints), minimal integration test (upload lifecycle) |
| Tooling | Ruff (lint), mypy (types), pytest, pre-commit hooks |
| CI | Workflow running lint + type + tests on PR |
| Documentation | Updated README (quick start), coding standards reference, M1 plan (this file), optional ADR(s) |

---

## 3. Scope Breakdown (Work Packages)

### 3.1 Repository & Tooling Setup
- Initialize backend and frontend directories (`/backend`, `/frontend`, or monorepo variant).
- Add `pyproject.toml` (dependencies: fastapi, uvicorn, pydantic, sqlalchemy/SQLModel, psycopg, boto3/minio client, python-multipart).
- Configure Ruff + mypy + pytest.
- Pre-commit hooks (format, lint, type).
- Add initial README sections: Overview, Stack, Quick Start (docker compose).

### 3.2 Database Schema (Initial)
Tables (minimum viable):
- `ingestion_runs`
  - id (uuid or bigint)
  - created_at
  - type (enum: ds_etc | instance_etc | app_bundle | single_conf)
  - label (nullable)
  - status (enum: pending | stored | failed | complete) – for now transitions: pending → stored
  - notes (nullable)
- `files`
  - id
  - run_id (FK)
  - path (for M1: archive filename only)
  - sha256
  - size_bytes
  - stored_object_key (reference to blob)

Migration file created & applied via Alembic.

### 3.3 Backend Application Skeleton
- `app/main.py`: FastAPI instance creation.
- `app/config.py`: Pydantic Settings (DB URL, storage backend, env).
- `app/db.py`: Session management.
- `app/models.py` / `app/schemas.py`: ORM + pydantic schemas.
- `app/routes/uploads.py`: Upload endpoints.
- `app/routes/runs.py`: Run listing & detail.
- `app/services/uploads.py`: Service-layer for ingestion run creation + blob storage.
- `app/storage/`:
  - `base.py` interface.
  - `local.py` or `s3.py` (MinIO-compatible).
- `app/logging.py`: Structured logging (JSON optional).
- `app/health.py`: Health probe.

### 3.4 Upload Flow (M1 Implementation)
1. Client sends multipart form:
   - file (tar/zip)
   - type (enum)
   - label (optional)
2. API:
   - Validate type.
   - Generate run record (status=pending).
   - Stream file to storage (compute sha256).
   - Create `files` entry with metadata.
   - Update run status → stored.
3. Response: run metadata (id, status, created_at).

(Parsing step stubbed—placeholder for parse trigger in later milestone.)

### 3.5 Frontend Skeleton
- Tech: React + Vite, TypeScript, Tailwind config.
- Structure: `src/components`, `src/pages`, `src/api`.
- Pages:
  - UploadPage: drag/drop (react-dropzone or native), select type, label, submit button, show result (run id).
  - RunsPage: table listing runs (id, type, created_at, status).
- API Client: lightweight wrapper (fetch with base URL env).
- State: React Query for `useRuns` / `useUpload`.
- Basic styling, responsive layout.

### 3.6 Configuration & Environments
- `.env.example` for backend (DB creds, storage path).
- Docker Compose:
  - `api`: mounts backend, reload.
  - `db`: Postgres 15 with volume.
  - `minio`: (optional) or use host volume path.
  - `frontend`: dev server.
  - `redis`: placeholder (not yet consumed).

Optional: a make target (e.g., `make dev`).

### 3.7 Observability (M1 Level)
- Request logging middleware (method, path, duration, status).
- Basic structured log formatter.
- `/health` returns { db: ok } if DB connection works.

### 3.8 Testing (M1)
- Unit tests:
  - Upload service (file hashing, run creation).
  - Models (simple create/select).
  - API endpoint tests (FastAPI TestClient).
- Integration:
  - Simulated upload tarball → assert run + file entry.
- Fixtures:
  - Temporary storage path.
  - Test DB (transaction rollback or ephemeral).
- Minimum coverage goal (optional): 70% lines for touched modules.

### 3.9 Quality Gates & CI
- GitHub Actions workflow:
  - Steps: checkout → set up Python → install deps → run ruff → mypy → pytest.
- Failing gates block merge.

### 3.10 Documentation
- Update README with:
  - Project summary.
  - Architecture snapshot (current milestone scope).
  - Quick start (docker compose up).
  - Upload API spec (example curl).
- This milestone plan stored in `notes/`.
- Add `CONTRIBUTING.md` (coding standards referencing `notes/github-instructions.md`).

---

## 4. Acceptance Criteria (Definition of Done)

1. `docker-compose up` launches all core services; frontend reachable; API health endpoint returns success.
2. `POST /v1/uploads` accepts a valid archive and returns JSON containing new run id and status=stored.
3. `GET /v1/runs` lists the created run.
4. Blob physically present in configured storage (locally or MinIO).
5. Database reflects `ingestion_runs` and `files` rows with correct metadata (hash, size).
6. Frontend:
   - Upload page performs successful upload and surfaces run id.
   - Runs page lists at least one run with correct status.
7. All lint & type checks pass; tests green in CI.
8. README instructions reproduce environment without undocumented steps.
9. Logging shows run id correlation for upload request.
10. Code adheres to PEP 8, has type hints, and each endpoint has at least one test.

---

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Premature over-engineering of parsing layer | Delays M1 | Keep parse entirely out; stub only |
| Storage abstraction churn | Refactors later | Define minimal `store_blob()` + return key interface now |
| Large upload memory usage | OOM | Stream to disk in chunks; avoid full in-memory buffering |
| Inconsistent schema evolution | Migration drift | Lock migrations early; PR review checklist |
| CI flakiness (DB readiness) | Slower dev | Add wait-for-db script or health check retries |

---

## 6. Sequenced Task Order (Suggested)

1. Repo & tooling scaffold (lint, type, test).
2. DB + migrations.
3. Storage interface & local implementation.
4. Backend models + services + upload endpoint.
5. Runs listing endpoint.
6. Logging & health endpoint.
7. Frontend scaffold + API client.
8. Upload page.
9. Runs page.
10. Tests (unit then integration).
11. CI workflow.
12. Documentation polish (README, CONTRIBUTING, this plan).

Parallelizable: Frontend scaffold can begin once API contract drafted.

---

## 7. Implementation Notes & Conventions

- Use UUID primary keys or bigint (choose early; UUID reduces future sharding concerns).
- Timestamps in UTC ISO8601.
- Pydantic v2 models for request/response; avoid exposing ORM models directly.
- Service-layer pattern: route → schema validation → service → persistence.
- Minimal domain naming consistency: `IngestionRun` (avoid `UploadRun` naming drift).

---

## 8. Future Hooks (Prepared in M1 but Not Implemented)

Foundation points that ease M2+:
- Keep `ingestion_runs.status` enum extensible (will add parsing states: parsing, normalized, resolved).
- Add optional `parent_run_id` column migration placeholder (nullable) for future diffs.
- Reserve `/v1/runs/{id}/parse` route path (not active yet).

---

## 9. Glossary (M1 Scope Terms)

| Term | Definition (M1 Context) |
|------|-------------------------|
| Ingestion Run | A single uploaded archive tracked in DB |
| Blob | Raw uploaded file stored in object/file storage |
| Run Status | Lifecycle marker (pending → stored in M1) |
| File Record | Metadata about the uploaded archive (not yet exploded contents) |

---

## 10. Estimated Effort (Rough Order of Magnitude)

| Work Package | Est. Person-Days |
|--------------|------------------|
| Repo/tooling + CI | 1 |
| DB + migrations | 0.5 |
| Storage + upload service | 1 |
| API endpoints & schemas | 1 |
| Frontend scaffold + upload UI | 1 |
| Runs list page | 0.5 |
| Testing (unit/integration) | 1 |
| Documentation & polish | 0.5 |
| Buffer / Risk | 0.5 |
| Total | ~7 days |

---

## 11. Summary

This milestone establishes the contract, persistence layer, and user-facing minimal workflow needed to progress confidently into parsing and normalization in Milestone 2. Success here is a stable, repeatable, and test-backed foundation.

---

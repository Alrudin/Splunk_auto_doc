# Milestone 1 Gap Analysis & Issue Mapping

Date: 2025-09-28
Author: @Alrudin (compiled with Copilot assistant)

## Purpose
This document captures the comparison between the Milestone 1 execution plan (notes/milestone-1-plan.md) and the currently tracked work in GitHub issues/PRs, and enumerates recommended new issues to fully cover the milestone scope.

## Source Inputs
- Milestone plan: `notes/milestone-1-plan.md`
- Retrieved open items at time of analysis:
  - Issue #8: "Add Docker Compose for all core services" (labels: documentation, Milestone-1)
  - PR #9 (WIP): Implements/adjusts docker-compose for core services (partial coverage of infra deliverable)
- No other M1-scoped issues existed at retrieval time.

## High-Level Summary
Only infrastructure/docker-compose work is presently represented. All other functional, testing, CI, documentation, and tracking tasks for M1 are not yet captured as discrete issues. Creating granular issues enables parallel progress, clearer acceptance tracking, and reduces risk of scope leakage.

## Plan Sections vs Tracking Status
| Plan Element / Deliverable | Present? | Covered By | Gap / Notes |
|----------------------------|----------|-----------|-------------|
| Infrastructure (docker compose: api, db, minio, redis, frontend placeholder) | Partial | Issue #8 / PR #9 | Frontend service placeholder & health checks likely incomplete |
| Backend application skeleton (structure, config, logging stub, health) | No | – | Needs dedicated issue |
| Database schema + migrations (`ingestion_runs`, `files`) | No | – | Alembic init & first migration |
| Storage abstraction (local/MinIO) | No | – | Interface + implementation |
| Upload ingestion endpoint POST /v1/uploads | No | – | Status transition pending→stored |
| Runs listing & detail endpoints | No | – | GET /v1/runs, /v1/runs/{id} |
| Logging & request middleware | No | – | Structured logs w/ run id correlation |
| Frontend scaffold (React/Vite/Tailwind) | No | – | Baseline layout & build |
| Frontend Upload Page | No | – | Drag & drop + metadata form |
| Frontend Runs Page | No | – | Table listing runs |
| Tooling & pre-commit (Ruff, mypy, pytest) | No | – | pyproject + hooks |
| Testing (unit + integration upload lifecycle) | No | – | Fixtures + coverage goal |
| CI pipeline (lint, type, test) | No | – | GitHub Actions workflow |
| Documentation updates (README, CONTRIBUTING, curl examples) | No | – | Architecture snapshot needed |
| ADR(s) for core decisions | No | – | Optional but recommended |
| Risk mitigations (DB readiness, streaming uploads) | No | – | Healthcheck/wait script + chunked streaming |
| Meta acceptance tracking issue | No | – | Checklist of DoD items |
| Environment helpers (.env.example, make targets) | No | – | Makefile / examples |

## Recommended New Issues (Proposed Titles & Scopes)
(Each should carry label: `Milestone-1`; add secondary labels: backend, frontend, infra, testing, documentation, ci, tooling as appropriate.)

1. Initialize Backend Application Skeleton
   - Create FastAPI structure (`app/main.py`, `config.py`, `db.py`, `models.py`/`schemas.py`, route modules) + basic logging + `/health`.
   - DoD: Server starts; `/health` returns JSON.

2. Implement Initial Database Schema & Alembic Migration
   - `ingestion_runs` and `files` tables per plan; initial migration committed.
   - DoD: Alembic upgrade applies successfully; tables verifiable.

3. Add Storage Abstraction (Local / MinIO)
   - `app/storage/base.py` + `local.py` (and optional MinIO client wrapper); `store_blob()` returns key.
   - DoD: Test storing sample file produces retrievable blob.

4. Implement Upload Ingestion Endpoint (POST /v1/uploads)
   - Multipart handling, run record creation (pending→stored), sha256 hashing, file metadata persistence.
   - DoD: Response contains run id + status=stored; DB + storage updated.

5. Implement Runs Listing & Detail Endpoints
   - `GET /v1/runs`, `GET /v1/runs/{id}` returning required fields.
   - DoD: After upload, runs appear & detail matches DB.

6. Add Structured Logging & Request Middleware
   - Timing, method, path, status; run id correlation where applicable.
   - DoD: Logs show structured entries for upload flow.

7. Frontend Scaffold (React + Vite + Tailwind + React Query)
   - Project structure, build config, API client wrapper.
   - DoD: Dev server serves placeholder page.

8. Frontend Upload Page
   - Drag/drop or file picker, type select, label, submit, display result.
   - DoD: Successful upload visually confirmed.

9. Frontend Runs Page
   - Table listing id, type, created_at, status; manual refresh or polling.
   - DoD: Displays newly created runs.

10. Configure Tooling & Pre-Commit Hooks
    - Ruff, mypy, pytest config; pre-commit with lint + type + tests (where feasible).
    - DoD: Pre-commit runs on staged files; passes in clean state.

11. Add Test Suite (Unit & Integration)
    - Fixtures (temp storage, test DB), unit (models, services), integration (full upload).
    - DoD: Tests pass; optional coverage >=70% for touched modules.

12. Set Up CI Workflow (Lint, Type, Tests)
    - GitHub Actions YAML; failing checks block merges.
    - DoD: Green run on main + PR gating.

13. Documentation & Contributor Guide Updates
    - README (summary, architecture snapshot, quick start, curl example), CONTRIBUTING (coding standards), `.env.example`.
    - DoD: Fresh clone + README steps lead to working environment.

14. Architecture Decision Record (ADR-001 Core Stack)
    - Rationale for FastAPI, storage abstraction, minimal schema, React stack.
    - DoD: ADR committed and referenced from README or CONTRIBUTING.

15. DB Readiness / Wait Strategy for Local & CI
    - Healthcheck or script ensuring Postgres is ready before migrations/tests.
    - DoD: No intermittent DB connection errors in CI.

16. Streamed Upload & Memory Safety
    - Chunked file write + hashing; avoid full in-memory buffering.
    - DoD: Large sample (within limits) processed with stable memory profile.

17. Milestone 1 Completion Tracking (Meta)
    - Checklist referencing all issue numbers and acceptance criteria items (1–10 from plan section 4).
    - DoD: Closed when all child issues done; each DoD item verified.

18. Coding Standards & Style Enforcement
    - Explicit PEP8, type hints, commit style; references `notes/github-instructions.md`.
    - DoD: CONTRIBUTING includes standards; CI enforces.

19. Enhance Health Endpoint (DB Status Reporting)
    - `/health` returns `{ db: ok }` when DB reachable; failure path logs error.
    - DoD: Simulated DB outage reflected in endpoint response/logs.

20. Environment & Make Targets
    - `.env.example` + `Makefile` (`make dev`, `make test`, `make lint`).
    - DoD: `make dev` launches full stack (post docker-compose updates).

## Suggested Sequencing (Derived from Plan Section 6)
1. Backend skeleton & tooling (#1, #10)
2. DB schema (#2)
3. Storage abstraction (#3)
4. Upload endpoint (#4) + logging (#6) + health enhancement (#19)
5. Runs endpoints (#5)
6. Frontend scaffold (#7)
7. Upload page (#8) & Runs page (#9)
8. Tests (#11) & streamed upload safety (#16)
9. CI pipeline (#12) + DB readiness (#15)
10. Documentation, ADR, standards, env helpers (#13, #14, #18, #20)
11. Meta tracking closure (#17)

## Acceptance Criteria Traceability
Each recommended issue maps directly to acceptance criteria items in Section 4 of the plan. The meta tracking issue (#17) should enumerate and check off the plan's DoD points:
- Environment up via docker compose (issues #8, #20)
- Upload lifecycle functional (#4, #3, #2)
- Run listing functional (#5)
- Blob persistence verified (#3, #4)
- DB rows persisted (#2, #4, #5)
- Frontend upload + runs pages (#8, #9, #7)
- Lint/type/tests green (#10, #11, #12)
- Reproducible README (#13, #20)
- Logging correlation (#6)
- Code style & typing (#10, #18)

## Next Steps
1. Create the set of issues using the above titles/descriptions.
2. Add them all to Milestone 1; apply appropriate labels.
3. Stand up meta tracking issue (#17) once others are created; backfill cross-links.
4. Begin implementation following sequencing.

---
Generated to preserve current state before issue creation.
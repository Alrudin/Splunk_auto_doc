# Milestone 2 Gap Analysis & Issue Mapping

Date: 2025-10-07 (status update: 2025-10-25)
Author: @Alrudin (compiled with Copilot assistant)

## Purpose

This document tracks alignment between the Milestone 2 plan (Parser & Normalization) and the currently tracked work in GitHub issues/PRs, and enumerates recommended issues to close the gaps. It will be updated as work progresses.

## Source Inputs

- Milestone plan (proposed): `notes/milestone-2-plan.md`
- Project overview: `notes/Project description.md`
- Milestone 1 completion baseline: `MILESTONE_1_COMPLETION.md`
- Milestone 1 plan: `notes/milestone-1-plan.md`

## High-Level Summary

Milestone 2 focuses on:

- Parsing Splunk `.conf` files into ordered stanzas with provenance
- Normalizing into typed tables (`inputs`, `props`, `transforms`, `indexes`, `outputs`, `serverclasses`)
- Background job to parse and persist results
- Minimal API + UI for triggering and viewing parsed counts

Current state: Core parsing and all typed projections are complete. Background worker (with retries) and the end-to-end normalization pipeline are complete. Remaining work centers on frontend UI for parse controls/visibility, CI updates, expanded observability, and documentation (ADR-002 and end-to-end examples).

---

## Plan Sections vs Tracking Status

| Plan Element / Deliverable                                                    | Present? | Covered By                                                         | Gap / Notes                                                                                         |
|-------------------------------------------------------------------------------|:--------:|--------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| Schema migrations: `stanzas` + typed tables + indexes                         |   Yes    | #50 (closed, completed)                                            | Delivered via Alembic migrations                                                                    |
| Parser core: files → ordered stanzas (comments, continuation, repeats)        |   Yes    | #52 (closed)                                                       | Tokenizer/assembler + comprehensive unit tests                                                      |
| Typed projections: inputs/props/transforms/indexes/outputs/serverclasses      |   Yes    | #54, #56, #57, #58, #59, #60 (all closed)                          | Completed for all six types with tests                                                              |
| Normalization pipeline: unpack → walk → parse → bulk insert                   |   Yes    | #70 (closed)                                                       | End-to-end orchestration complete                                                                   |
| Background worker: Redis + Celery/RQ, parse task with retries                 |   Yes    | #67 (worker service closed), #68 (retries/failure handling closed) | Worker service, retries/backoff, visibility timeouts implemented                                    |
| Run status lifecycle: stored → parsing → normalized → complete/failed         |   Yes    | Implemented with status transitions                                | Status enum extended with notes/errors                                                              |
| API: trigger parse, status, summary, typed listings                           |   Yes    | Complete - all endpoints implemented including parse trigger       | POST /runs/{id}/parse endpoint implemented; status/summary/typed listings live                      |
| Frontend: Run detail “Parse” button, status polling, counts panel             |   No     | –                                                                  | Minimal UI to monitor and inspect parsed artifacts pending                                          |
| Observability: structured logs, metrics, extraction guardrails                |  Partial | #67, #68, #70 (closed)                                             | Worker metrics/logs and pipeline guardrails in place; consider dashboards and broader instrumentation |
| Fixtures & tests: golden fixtures, property tests, integration                |   Yes    | #52, #54, #56, #57, #58, #59, #60, #70 (closed)                    | Parser + typed projection + pipeline covered                                                        |
| CI pipeline updates: parser/unit/property/integration                         |   No     | –                                                                  | Add jobs; optional performance smoke                                                                |
| Documentation: parser spec, normalization model, ADR-002                      |  Partial | #52, typed projection issues, #70 (closed)                         | Parser spec and normalization model draft exist; ADR-002 and end-to-end examples outstanding        |

---

## Recommended New/Remaining Issues (M2)

- Milestone 2 Meta Tracking Issue (Parser & Normalization)
- Frontend: Add parse trigger on Run detail; live status; parsed counts display
- Observability: extend system-wide metrics/dashboards; performance budgets in CI
- CI updates: add integration jobs for worker/pipeline; optional performance smoke
- Documentation: ADR-002 (parser approach & trade-offs); end-to-end examples across all types

Note: Completed and removed from remaining list — Schema migrations (#50), Parser core (#52), Typed projections (#54/#56/#57/#58/#59/#60), Background worker and retries (#67/#68), Normalization pipeline (#70), and API endpoints (parse/status/summary/listings).

---

## Risks & Mitigations (M2)

- Zip/Tar bombs or path traversal
  - Mitigation: enforce limits on uncompressed size, file count, depth; reject symlinks; sanitize paths.
- Order/precedence correctness
  - Mitigation: preserve stanza and key order; property tests asserting invariants.
- Performance on large configs
  - Mitigation: streaming parse, bulk inserts, fixture-based benchmarks; regressions tracked in CI.
- Worker reliability
  - Mitigation: retries, idempotent tasks keyed by run_id, visibility timeouts, structured error reporting.

---

## Acceptance Criteria (Definition of Done)

- Upload → parse → normalized typed records persisted for supported `.conf` types.
- `ingestion_runs.status` transitions: stored → parsing → normalized → complete (or failed with error in notes).
- API exposes parse trigger/status/summary; typed listings with pagination and filters.
- Frontend can trigger parse for a run and display live status + counts.
- Parser passes unit/property tests for comments, continuation lines, repeated keys, and order preservation.
- Golden fixtures produce expected normalized outputs; integration tests green.
- CI includes parser/unit/property/integration jobs; all green on main.
- Documentation published: parser spec, normalization model, ADR-002.
- Extraction safety checks implemented and covered by tests.

---

## Status Rollup (latest)

- Planning: In progress
- Implementation: Parser core complete (#52); Typed projections complete (#54/#56/#57/#58/#59/#60); Background worker + retries complete (#67/#68); Normalization pipeline complete (#70)
- Issues/PRs (closed relevant to M2):
  - #50 — Schema migrations: stanzas + typed tables + indexes
  - #52 — Parser core
  - #54 — Typed projection: inputs.conf
  - #56 — Typed projection: props.conf
  - #57 — Typed projection: outputs.conf
  - #58 — Typed projection: serverclass.conf
  - #59 — Typed projection: indexes.conf
  - #60 — Typed projection: transforms.conf
  - #67 — Background worker service
  - #68 — Worker retries and failure handling
  - #70 — Normalization pipeline
- Blockers: None identified

---

## Update Log

- 2025-10-25: VERIFICATION COMPLETE - All API endpoints for typed listings fully implemented and tested:
  - ✅ GET /runs/{id}/inputs - with pagination (page, per_page) and filtering (app, scope, layer, stanza_type, index)
  - ✅ GET /runs/{id}/props - with pagination and filtering (target)
  - ✅ GET /runs/{id}/transforms - with pagination and filtering (name)
  - ✅ GET /runs/{id}/indexes - with pagination and filtering (name)
  - ✅ GET /runs/{id}/outputs - with pagination and filtering (group_name)
  - ✅ GET /runs/{id}/serverclasses - with pagination and filtering (name, app, scope, layer)
  - ✅ All endpoints return entity data with full provenance fields (run_id, source_path, app, scope, layer where applicable)
  - ✅ Comprehensive test coverage in `backend/tests/test_typed_listings.py` (22 test functions covering all endpoints)
  - ✅ Full API documentation in README.md (lines 888-950+) with query parameter examples
  - All acceptance criteria from issue met and verified
- 2025-10-25: Implemented POST /runs/{id}/parse endpoint to trigger background parsing jobs. Added comprehensive tests (test_parse_trigger.py) covering success cases, idempotency, error handling, and logging.
- 2025-10-25: Implemented GET /runs/{id}/summary endpoint with entity counts for all parsed types. Added tests and documentation.
- 2025-10-25: Implemented API endpoints for typed listings (inputs, props, transforms, indexes, outputs, serverclasses) with pagination and filtering. Updated README with endpoint documentation. Verified provenance fields are included.
- 2025-10-25: Marked background worker (#67), retries/failure handling (#68), and normalization pipeline (#70) as completed; updated statuses and notes accordingly.
- 2025-10-23: Typed projections completed for all types (#54, #56, #57, #58, #59, #60).
- 2025-10-19: Marked schema migrations as Present=Yes (#50 closed) and parser core complete (#52 closed).
- 2025-10-07: Initial gap analysis scaffold created for M2.
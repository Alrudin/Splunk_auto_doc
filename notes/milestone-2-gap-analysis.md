# Milestone 2 Gap Analysis & Issue Mapping

Date: 2025-10-07 (status update: 2025-10-19)
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

Current state: Planning initiated. Issues for M2 work are being opened from “Recommended New/Remaining Issues.”

---

## Plan Sections vs Tracking Status

| Plan Element / Deliverable                                                    | Present? | Covered By                        | Gap / Notes                                                                 |
|-------------------------------------------------------------------------------|:--------:|-----------------------------------|------------------------------------------------------------------------------|
| Schema migrations: `stanzas` + typed tables + indexes                         |   Yes    | Issue #50 (closed, completed)     | Delivered via Alembic migrations (002/003). Docs updated; unblock downstream |
| Parser core: files → ordered stanzas (comments, continuation, repeats)        |   No     | –                                 | Implement tokenizer/assembler + comprehensive unit tests                     |
| Typed projections: inputs/props/transforms/indexes/outputs/serverclasses      |   No     | –                                 | Map stanzas to typed rows; validate Splunk-specific rules                    |
| Normalization pipeline: unpack → walk → parse → bulk insert                   |   No     | –                                 | Service orchestration, provenance, performance via bulk insert               |
| Background worker: Redis + Celery/RQ, parse task with retries                 |   No     | –                                 | Worker service + task wiring + observability                                 |
| Run status lifecycle: stored → parsing → normalized → complete/failed         |   No     | –                                 | Extend enums/values and transitions; persist summary counts                  |
| API: trigger parse, status, summary, typed listings                           |   No     | –                                 | Endpoints: POST /runs/{id}/parse, GET /parse-status, GET /summary, listings  |
| Frontend: Run detail “Parse” button, status polling, counts panel             |   No     | –                                 | Minimal UI to monitor and inspect parsed artifacts                           |
| Observability: structured logs, metrics, extraction guardrails                |   No     | –                                 | Time metrics, per-file progress logs; safety checks for zip/tar              |
| Fixtures & tests: golden fixtures, property tests, integration                |   No     | –                                 | Add curated etc/ samples + property tests (order, last-wins)                 |
| CI pipeline updates: parser/unit/property/integration                         |   No     | –                                 | Add jobs; optional performance smoke                                         |
| Documentation: parser spec, normalization model, ADR-002                      |   No     | –                                 | Docs for grammar/ERD; ADR capturing parser approach                          |

---

## Recommended New/Remaining Issues (M2)

- Milestone 2 Meta Tracking Issue (Parser & Normalization)
- Parser core: robust `.conf` parser (comments, line continuations, ordered keys, repeated keys)
- Typed projection mappers for inputs/props/transforms/indexes/outputs/serverclasses
- Normalization pipeline: unpack → parse → bulk insert with provenance and counts
- Background worker: Redis + Celery/RQ service; `parse_run(run_id)` task with retries/backoff
- API endpoints: POST /runs/{id}/parse; GET /runs/{id}/parse-status; GET /runs/{id}/summary; typed listings
- Frontend: Add parse trigger on Run detail; live status; parsed counts display
- Observability & safety: structured logs for parse lifecycle; extraction guardrails (size/file-count/depth, disallow symlinks)
- Fixtures and tests: golden fixtures; property tests; end-to-end integration (upload → parse → assert DB)
- CI updates: add parser/test jobs; optional performance smoke
- Documentation: `docs/parser-spec.md`, `docs/normalization-model.md`, ADR-002 (parser approach & trade-offs)

Note: The Alembic migration work for schema migrations is complete via Issue #50 (closed) and removed from the remaining issues list.

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
- Implementation: Started (schema migrations complete)
- Issues/PRs:
  - Issues closed: #50
  - Pull requests: none reported in latest retrieval
- Blockers: None identified

---

## Update Log

- 2025-10-19: Marked schema migrations as Present=Yes and noted Issue #50 closed/completed.
- 2025-10-07: Linked Issue #50 for schema migrations; no open pull requests reported in latest retrieval.
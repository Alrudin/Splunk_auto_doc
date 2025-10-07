# Milestone 2 Plan – Parser & Normalization

Milestone Code: M2
Focus Window: 2–3 weeks
Primary Goal: Parse uploaded Splunk .conf content, normalize it into a relational schema, and expose minimal APIs and UI to inspect parsed counts and artifacts.

---

## 1. Objectives

1. Implement a robust Splunk .conf parser:
   - Handle comments, line continuations, repeated keys, stanza ordering.
   - Preserve source metadata (file path, app, scope: default/local, layer: system/app).
2. Normalize parsed content into database tables:
   - `stanzas` (generic) and typed projections: `inputs`, `props`, `transforms`, `indexes`, `outputs`, `serverclasses`.
3. Establish a parsing job flow:
   - Trigger from API, run in a background worker (Redis + Celery/RQ), update run status lifecycle: `stored → parsing → normalized → complete`.
4. Provide minimal APIs and UI to:
   - Trigger/monitor parse.
   - Return parsed counts and simple listings for typed entities.
5. Add golden fixtures, unit/property tests for parser correctness and performance.
6. Document the parsing rules, normalization model, and developer workflow.

Out of scope (deferred to M3+):

- Host/app resolution from serverclass membership (M3).
- Routing resolver to compute effective index/sourcetype (M4).
- Rich UI explorers/graphs (M5).

---

## 2. Deliverables

- Backend
  - Parser module with tests and fixtures.
  - Normalization pipeline to persist stanzas and typed tables.
  - Background worker setup and task to parse runs.
  - API endpoints for parse control and retrieval of counts/artifacts.
- Database
  - Alembic migrations for `stanzas`, typed tables, and indexes.
  - Status transitions expanded in `ingestion_runs`.
- Frontend
  - Simple “Parse” action on Run detail.
  - Run detail shows parse status and parsed counts.
- Tooling/CI
  - Parser test suite (unit, property, integration) in CI.
  - Performance budget checks (optional).
- Documentation
  - Parser spec and normalization model docs.
  - Developer runbook for local/CI parsing.

---

## 3. Architecture Changes

- Introduce `app/parser/` with:
  - Tokenizer + line reader with continuation handling.
  - Stanza assembler preserving order.
  - Typers mapping stanzas → typed rows.
- Add `app/services/parse_service.py`:
  - Orchestrates unpack → walk → parse → normalize → commit.
- Background jobs:
  - `parse_run(run_id)` task in `app/worker/tasks.py`.
  - Redis-backed queue using Celery (default) or RQ as a lighter option.
- Status lifecycle:
  - `stored → parsing → normalized → complete` or `failed` with `notes`.

---

## 4. Database Schema Evolution

Alembic migration IDs: `002_stanzas_and_typed`, `003_indexes_and_perf`.

New tables:

- stanzas
  - id (PK), run_id (FK), file_id (FK)
  - conf_type (inputs|props|transforms|indexes|outputs|serverclasses|other)
  - name (stanza header)
  - app, scope (default|local), layer (system|app)
  - order_in_file (int), source_path (full path), raw_kv JSONB
- inputs
  - id (PK), run_id (FK), source_path, stanza_type, index, sourcetype, disabled, kv JSONB, app, scope, layer
- props
  - id (PK), run_id (FK), target (sourcetype or source), transforms_list (array), sedcmds (array), kv JSONB
- transforms
  - id (PK), run_id (FK), name, dest_key, regex, format, writes_meta_index bool, writes_meta_sourcetype bool, kv JSONB
- indexes
  - id (PK), run_id (FK), name, kv JSONB
- outputs
  - id (PK), run_id (FK), group_name, servers JSONB, kv JSONB
- serverclasses
  - id (PK), run_id (FK), name, whitelist JSONB, blacklist JSONB, app_assignments JSONB, kv JSONB

Indexes:

- B-tree: (run_id, conf_type, name), (run_id, app, scope, layer)
- GIN: raw_kv, kv for JSONB search
- Foreign keys: cascade on run delete

---

## 5. Parsing Rules (Splunk-Specific)

- Comments start with `#` (ignore), preserve inline comments when safe in evidence.
- Line continuation: trailing `\` merges with next line.
- Stanza header: `[header]` starts a new stanza; headers can include wildcards and tokens.
- Repeated keys: preserve last-wins within same stanza; also record ordered list for evidence.
- Props/transforms ordering matters; preserve stanza order and intra-stanza key order.
- Scope/layer detection from path:
  - `.../apps/<app>/(default|local)/...` → app + scope
  - `.../system/(default|local)/...` → system + scope
- Normalize keys to canonical forms (case-sensitive where Splunk is).
- Security: sanitize paths, disallow traversal outside extraction root.

---

## 6. Normalization Pipeline

1. Unpack archive to a secure temp dir (guard against zip/tar bombs).
2. Walk tree to collect .conf files of interest: inputs, props, transforms, outputs, indexes, serverclass.
3. For each file:
   - Parse into ordered stanzas and raw_kv.
   - Emit `stanzas` rows with metadata.
4. Typed projection:
   - inputs: detect stanza types (monitor://, tcp://, udp://, script://, WinEventLog://), extract common fields (index, sourcetype, disabled).
   - props: collect TRANSFORMS-*, SEDCMD-* in stanza order; determine target.
   - transforms: extract DEST_KEY, REGEX, FORMAT, detect index/sourcetype writes.
   - outputs: derive groups and server lists.
   - indexes: names + kv.
   - serverclasses: names, whitelist/blacklist, app assignments.
5. Bulk insert with SQLAlchemy core for performance.
6. Update `ingestion_runs.status` → `normalized` then `complete` upon success; write summary counts to `notes`.

---

## 7. Background Worker

- Default: Celery + Redis
  - New service: `worker` in docker-compose.
  - Task: `parse_run(run_id)`.
  - Retries with exponential backoff on transient errors.
- API enqueues task; idempotent by run_id (no duplicate processing).
- Observability: log parse duration, counts, and exceptions.

---

## 8. API Design (/v1)

- POST /runs/{id}/parse
  - 202 Accepted; returns job id or request id.
- GET /runs/{id}/parse-status
  - status: stored|parsing|normalized|complete|failed; error message if any.
- GET /runs/{id}/summary
  - counts: stanzas, inputs, props, transforms, outputs, indexes, serverclasses.
- GET /runs/{id}/inputs?app=&scope=&layer=&q=
- GET /runs/{id}/props?target=&app=&q=
- GET /runs/{id}/transforms?name=&q=
- GET /runs/{id}/indexes
- GET /runs/{id}/outputs
- GET /runs/{id}/serverclasses

Pagination (limit/offset) and simple filtering supported.

---

## 9. Frontend Additions

- Run Detail page:
  - “Parse” button (disabled if already complete).
  - Status badge with live polling while parsing.
  - Summary counts panel after completion.
- Optional: simple tables with pagination for typed entities (dev toggle).

---

## 10. Observability & Ops

- Structured logs around parse lifecycle:
  - start, per-file progress, totals, duration.
- Metrics (optional): parse duration histogram, stanza counts.
- Health: worker liveness/readiness endpoints.
- Safety:
  - Extraction guardrails: max total uncompressed bytes, max file count, depth limit, disallow symlinks, path traversal checks.

---

## 11. Testing Strategy

- Unit tests
  - Tokenizer and continuation lines.
  - Stanza parsing across odd whitespace, comments, repeated keys.
  - Typers for inputs/props/transforms/outputs/indexes/serverclasses.
- Property tests
  - Last-wins semantics for repeated keys.
  - Order preservation invariants for props/transforms.
- Golden fixtures
  - Curated etc/ samples (HF, UF, Indexer, DS).
  - Expected JSON snapshots per typed table.
- Integration tests
  - Upload → parse → DB assertions for counts and representative rows.
  - Worker task execution path (synchronous test harness).
- Performance checks
  - 10k+ stanzas fixture: target parse < 10s on dev machine, memory steady.

---

## 12. CI Pipeline Updates

- New job: parser unit + property tests.
- Integration job boots db + redis (+ worker where needed).
- Optional: performance smoke with smaller limit (skipped on PR, run on schedule).

---

## 13. Documentation

- docs/parser-spec.md — grammar, rules, edge cases.
- docs/normalization-model.md — ERD, field semantics, examples.
- README — new endpoints, local worker instructions.
- CONTRIBUTING — how to add fixtures, write parser tests.
- ADR-002 — Parser approach and trade-offs (native parser vs libraries).

---

## 14. Risks & Mitigations

- Zip/Tar bombs → strict extraction limits and safe lib usage.
- Splunk quirks (tokens/macros) → store as-is, flag unresolved/dynamic.
- Ordering semantics → preserve stanza and key order, assert in tests.
- Performance regressions → bulk inserts, streaming read, benchmark fixtures.
- Worker flakiness → retries, idempotent task, visibility timeouts (Celery acks late).

---

## 15. Sequenced Task Order

1. Schema migrations: `stanzas` and typed tables + indexes.
2. Parser core (files → stanzas) + unit tests.
3. Typed projection functions + tests.
4. Normalization pipeline integration (bulk insert) + integration tests.
5. Background worker service (Celery + Redis), task wiring.
6. API endpoints for parse trigger/status/summary.
7. Frontend Run detail: parse button + status + counts.
8. Observability: logs, metrics; extraction safety.
9. Golden fixtures + property tests.
10. Documentation (specs, model, ADR-002).
11. CI updates and performance smoke.

Parallelizable: Parser core and migrations can proceed in tandem; frontend can begin after API contract draft.

---

## 16. Acceptance Criteria (Definition of Done)

1. Upload → parse → normalized records persisted for all supported .conf types.
2. `ingestion_runs.status` transitions through parsing states and ends in `complete`.
3. API exposes parse status and summary counts; lists typed entities with filters.
4. Frontend can trigger parse and show status/counters for a run.
5. Parser handles comments, continuation, repeated keys, and preserves ordering.
6. Golden fixture tests pass with expected normalized outputs.
7. CI runs green: lint, type, unit/property, integration.
8. Documentation published: parser spec, normalization model, ADR-002.
9. Extraction safety checks validated with tests.
10. Performance target met on reference fixture; no unbounded memory growth.

---

## 17. Estimated Effort (Rough Order of Magnitude)

| Work Package                            | Est. Person-Days |
|-----------------------------------------|------------------:|
| Schema migrations + ERD refinement      | 1.0               |
| Parser core (files → stanzas)           | 2.0               |
| Typed projections + tests               | 2.0               |
| Normalization pipeline + bulk insert    | 1.5               |
| Background worker + wiring              | 1.0               |
| API endpoints + contracts               | 1.0               |
| Frontend (parse + status + counts)      | 1.0               |
| Fixtures, property + integration tests  | 2.0               |
| Docs (specs, ADR-002, README)           | 1.0               |
| Buffer / Risk                           | 1.0               |
| Total                                   | ~13.5 days        |

---

## 18. Notes & Conventions

- Preserve source provenance on every row: run_id, file_id, app, scope, layer, source_path, order.
- Keep parser pure/deterministic; side effects in normalization layer.
- Prefer SQLAlchemy Core bulk operations for speed.
- Validate inputs; never trust archive contents (path traversal, symlinks).
- Keep consistent JSONB kv storage for unknown/less-typed attributes.

---

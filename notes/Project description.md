# Splunk Conf Parser Web Application  
Plan & Architecture

---

## High-Level Goals
- Parse Splunk `.conf` files (apps and Deployment Server) to derive **Host → App → Input → (Sourcetype, Index, Dest Index)** mappings, including **props/transforms routing** and **serverclass client membership**.  
- Support **multiple uploads** (full `etc/` directories, additional app bundles, or single confs) and **recompute** paths incrementally.  
- Provide a React web UI to upload, browse, search, and visualize **data paths** and **effective configuration** over time.  

---

## System Design (Overview)
**Core idea**: Normalize all `.conf` content into a relational model, then build a deterministic **resolution engine** that computes final routings per host based on Splunk’s precedence rules.  

**Major components**
1. **Web UI (React + Tailwind)**: upload wizard, parsing job status, host/app browser, data-path explorer, diffs, and visual graphs.  
2. **API (Python/FastAPI)**: receives uploads, stores files, runs parsing/resolve jobs, exposes query endpoints.  
3. **Parser/Resolver (Python)**:
   - Splunk `.conf` parser (stanzas, key merging, comments, repeated keys).  
   - Precedence/overlay engine.  
   - Routing resolution: Inputs → Props → Transforms → Outputs.  
   - Serverclass membership resolution.  
4. **DB (PostgreSQL)**: normalized storage with versioning.  
5. **Object Storage**: raw upload blobs.  
6. **Task runner**: Celery/Arq/RQ for parsing jobs.  

---

## Architecture Pattern
- **Backend**: FastAPI (REST), service-layer pattern; background worker.  
- **Frontend**: React SPA; state via React Query.  
- **Data pipeline**: ETL (Extract → Normalize → Resolve → Persist results).  
- **Idempotent versioning**: each upload = **IngestionRun** snapshot.  

---

## Data Flow
1. **Upload**: User submits tar/zip of etc/ or conf files.  
2. **Ingest**: API stores blob, creates IngestionRun.  
3. **Normalize**: Persist stanzas to typed tables (`inputs`, `props`, `transforms`, …).  
4. **Resolve**:  
   - Determine host membership.  
   - Apply precedence.  
   - Derive Input → Sourcetype → Index paths.  
5. **Persist Results**: Store in DB (`host_data_paths`).  
6. **Serve UI**: Host/App/Index explorers, tables, graphs.  

---

## Technical Stack
**Frontend**
- React + Vite  
- TailwindCSS (+ Headless UI/shadcn)  
- React Router, React Query, Zod  
- d3 or Cytoscape.js for graphs  

**Backend**
- Python 3.11+  
- FastAPI (pydantic v2)  
- Celery + Redis (optional)  
- File unpacking via `libarchive`/`shutil`  
- Custom parser or `configobj` with Splunk-specific logic  

**Storage**
- PostgreSQL 15+  
- Object storage: disk or S3-compatible  

**Deploy**
- Docker Compose (api, worker, db, redis, ui, minio)  

---

## Parsing & Resolution Rules
1. **Config precedence**: `system/local` > `app/local` > `app/default` > `system/default`.  
2. **inputs.conf**: monitors, tcp/udp, etc. Keys: `index`, `sourcetype`, etc.  
3. **props.conf**: `TRANSFORMS-*` (index-time), `SEDCMD-*`.  
4. **transforms.conf**: `DEST_KEY=_MetaData:Index` for routing, `MetaData:Sourcetype` for sourcetype rewrites.  
5. **outputs.conf**: indexer groups/targets.  
6. **indexes.conf**: defines indexes.  
7. **serverclass.conf**: whitelist/blacklist rules, app assignment.  
8. **Conflict resolution**: precedence or first-match as per Splunk.  
9. **Edge cases**: macros, disabled stanzas, tokens flagged.  

---

## Database Design (ERD Summary)
**Core entities**
- `ingestion_runs`  
- `files`  
- `stanzas` (generic)  
- `inputs`, `props`, `transforms`, `indexes`, `outputs`, `serverclasses` (typed views/tables)  

**Resolution products**
- `hosts`  
- `host_memberships`  
- `host_apps`  
- `host_effective_inputs`  
- `host_data_paths`  

Indexes: B-tree and GIN for speed.  

---

## Resolver Algorithm
1. Resolve hosts from serverclass patterns.  
2. Assign apps per host.  
3. Build effective layered configs.  
4. Compute routing per input:
   - Base index/sourcetype.  
   - Apply transforms.  
   - Assign outputs group.  
5. Validate indexes, disabled inputs.  

---

## API Design
`/v1` endpoints:  
- `POST /uploads`  
- `GET /runs/:id`  
- `POST /runs/:id/parse`  
- `GET /hosts`, `/hosts/:id/paths`  
- `GET /apps`, `/indexes`, `/serverclasses`  
- `GET /graph/host/:id`  
- `GET /evidence/:pathId`  

Auth: JWT, roles (viewer/contributor/admin).  

---

## Frontend UX
- **Upload Wizard**: select type, progress, summary.  
- **Explore Tabs**: Hosts, Apps, Indexes, Serverclasses, Runs.  
- **Host Detail**: effective apps, data-path table, evidence drawer, graph.  
- **Diffs**: run-to-run comparisons.  
- **Search**: across sourcetype, index, app.  

---

## Implementation Milestones
- **M1**: Skeleton + upload pipeline.  
- **M2**: Parser + normalization.  
- **M3**: DS serverclass resolution.  
- **M4**: Routing resolver.  
- **M5**: UI explore & graph.  
- **M6**: Diffs & validation.  
- **M7**: Hardening & auth.  

---

## Testing Strategy
- Golden fixtures of real Splunk etc/.  
- Property tests for precedence invariants.  
- Performance runs (10k+ stanzas).  

---

## Observability & Ops
- Structured logs, metrics, health checks.  
- Backups for DB + storage.  

---

## Security
- Treat uploads as sensitive.  
- Optional virus scan.  
- Access control per project/workspace.  

---

## Splunk Nuances
- Only index-time rules affect routing.  
- Preserve transform order.  
- Report unresolved macros/tokens.  
- Outputs groups used for topology, not index renaming.  

---

## Deliverables
- Containerized dev stack.  
- Minimal UI to upload and see parsed counts.  
- Example host data-path table.  

| Host | Source Path | Effective Sourcetype | Effective Index | Outputs Group | Evidence |
|------|-------------|----------------------|-----------------|---------------|----------|

---

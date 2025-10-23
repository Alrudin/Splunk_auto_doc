# Quick Reference: Retry and Failure Handling

## For Developers

### When to Use Which Error Type

```python
from app.worker.exceptions import PermanentError, TransientError

# Use PermanentError when:
if archive_corrupted or invalid_format or missing_data:
    raise PermanentError("Archive is corrupted")

# Use TransientError when:
if network_timeout or db_connection_lost or service_unavailable:
    raise TransientError("Database connection lost")
```

### Check Job Status

```bash
# Get detailed status
curl http://localhost:8000/v1/worker/runs/42/status

# Get aggregated metrics
curl http://localhost:8000/v1/worker/metrics
```

### Monitor Task Progress

```python
from app.models.ingestion_run import IngestionRun

run = db.query(IngestionRun).get(run_id)

# Check status
print(run.status)  # pending, stored, parsing, complete, failed

# Check retry count
print(f"Retries: {run.retry_count}/3")

# Check last activity
print(f"Last heartbeat: {run.last_heartbeat}")

# Check errors
if run.error_message:
    print(f"Error: {run.error_message}")
    print(f"Trace: {run.error_traceback}")

# Check metrics
if run.metrics:
    print(f"Duration: {run.metrics['duration_seconds']}s")
    print(f"Files: {run.metrics['files_parsed']}")
    print(f"Stanzas: {run.metrics['stanzas_created']}")
```

## For Operations

### Common Error Patterns

| Error Message | Type | Action |
|--------------|------|--------|
| "Invalid archive format" | Permanent | Re-upload with valid format |
| "No files found" | Permanent | Check archive contents |
| "Storage retrieval failed" | Transient | Wait for auto-retry |
| "Database connection" | Transient | Check DB connectivity |
| "Failed after 3 retries" | Exhausted | Fix infra, re-upload |

### Troubleshooting Checklist

1. **Check run status**:
   ```bash
   curl http://localhost:8000/v1/worker/runs/{id}/status
   ```

2. **Check worker health**:
   ```bash
   curl http://localhost:8000/v1/worker/health
   ```

3. **Check worker logs**:
   ```bash
   docker compose logs -f worker
   ```

4. **Check metrics**:
   ```bash
   curl http://localhost:8000/v1/worker/metrics
   ```

5. **Review error details**:
   - Look at `error_message` for summary
   - Check `error_traceback` for debugging
   - Review `retry_count` to see attempts

### Retry Schedule

| Attempt | Delay | Total Time |
|---------|-------|------------|
| 1 | 0s | 0s |
| 2 | 60s | 1m |
| 3 | 180s | 4m |
| 4 | 600s | 14m |
| Fail | - | - |

### Alerting Thresholds

```yaml
alerts:
  high_failure_rate:
    threshold: 10%  # of jobs in last hour
    action: "Check infrastructure"
  
  retry_exhaustion:
    threshold: 5 jobs  # with 3 retries in last hour
    action: "Review error logs"
  
  stuck_tasks:
    threshold: 5 minutes  # since last heartbeat
    action: "Restart worker"
  
  no_workers:
    threshold: 1  # active workers
    action: "Start worker service"
```

## For Testing

### Run Integration Tests

```bash
# All retry/failure tests
pytest backend/tests/test_retry_failure_handling.py -v

# Specific test
pytest backend/tests/test_retry_failure_handling.py::test_permanent_error_no_retry -v

# With coverage
pytest backend/tests/test_retry_failure_handling.py --cov=backend/app/worker --cov-report=term
```

### Simulate Errors

```python
from app.worker.exceptions import PermanentError, TransientError

# Simulate permanent error
def mock_storage():
    raise PermanentError("Simulated permanent error")

# Simulate transient error
def mock_db():
    raise TransientError("Simulated network timeout")
```

## Architecture Quick View

```
Upload → Store → Parse Task
                     │
                     ├─ Success → COMPLETE
                     │
                     ├─ PermanentError → FAILED (no retry)
                     │
                     └─ TransientError → Retry 1 → 2 → 3
                                              │
                                              └─ FAILED (exhausted)
```

## Key Metrics

- **retry_count**: 0-3 (number of retry attempts)
- **duration_seconds**: Task execution time
- **files_parsed**: Number of .conf files processed
- **stanzas_created**: Number of stanzas inserted
- **error_type**: permanent | transient | timeout | unexpected

## Database Fields

```sql
-- ingestion_runs table
task_id VARCHAR(255)           -- Celery task ID
retry_count INTEGER            -- 0-3
error_message TEXT             -- Human-readable error
error_traceback TEXT           -- Full Python trace
last_heartbeat TIMESTAMP       -- Last activity
started_at TIMESTAMP           -- Task start
completed_at TIMESTAMP         -- Task end
metrics JSONB                  -- Execution metrics
```

## API Response Example

```json
{
  "id": 42,
  "status": "failed",
  "task_id": "abc-123",
  "retry_count": 3,
  "error_message": "Failed after 3 retries: Connection timeout",
  "error_traceback": "Traceback...",
  "started_at": "2024-01-15T10:00:00Z",
  "last_heartbeat": "2024-01-15T10:14:30Z",
  "completed_at": "2024-01-15T10:15:00Z",
  "metrics": {
    "duration_seconds": 900,
    "retry_count": 3,
    "error_type": "transient_exhausted"
  }
}
```

## Links

- Implementation: `RETRY_FAILURE_IMPLEMENTATION.md`
- Flow Diagrams: `RETRY_FLOW_DIAGRAMS.md`
- Worker Setup: `docs/worker-setup.md`
- Data Model: `docs/normalization-model.md`

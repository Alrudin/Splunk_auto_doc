# Worker Service Setup and Configuration

This document describes the background worker service for asynchronous parsing and processing of Splunk configuration uploads.

## Overview

The worker service processes uploaded configuration archives asynchronously using Celery with Redis as the message broker. This design allows the API to remain responsive while parsing large configuration bundles.

## Architecture

```
┌─────────────┐         ┌──────────┐         ┌─────────────┐
│   API       │         │  Redis   │         │   Worker    │
│             │────────▶│  Broker  │────────▶│   Service   │
│ (FastAPI)   │ Enqueue │          │  Fetch  │  (Celery)   │
└─────────────┘         └──────────┘         └─────────────┘
      │                                              │
      │                                              │
      └──────────────────────────────────────────────┘
                    PostgreSQL Database
```

## Components

### 1. Celery Application (`app/worker/celery_app.py`)

Configures the Celery application with:
- **Broker**: Redis for task queue management
- **Result Backend**: Redis for storing task results
- **Task Settings**: Timeouts, retries, and execution configuration
- **Logging**: Structured logging for task lifecycle

### 2. Parse Task (`app/worker/tasks.py`)

The `parse_run(run_id)` task:
1. Retrieves the uploaded archive from storage
2. Extracts configuration files
3. Parses each `.conf` file using `ConfParser`
4. Persists parsed stanzas to the database
5. Updates run status to `COMPLETE` or `FAILED`

**Key Features**:
- **Idempotent**: Safe to retry if interrupted
- **Retry Logic**: Exponential backoff (3 retries, up to 10 minutes between retries)
- **Error Handling**: Graceful failure with detailed error messages
- **Progress Tracking**: Updates run status throughout execution

### 3. Worker Health Endpoint (`/v1/worker/health`)

Monitors worker status and availability:
- Active worker count
- Running tasks
- Worker statistics

## Setup

### Prerequisites

- Docker and Docker Compose
- Redis (included in docker-compose.yml)
- PostgreSQL database

### Environment Variables

Add these to your `.env` file or environment:

```bash
# Redis/Celery Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/splunk_auto_doc

# Storage Configuration
STORAGE_BACKEND=local
STORAGE_PATH=/app/storage
```

### Running with Docker Compose

The worker service is included in `docker-compose.yml`:

```bash
# Start all services (API, worker, database, Redis)
docker compose up

# Start in detached mode
docker compose up -d

# View worker logs
docker compose logs -f worker

# Stop all services
docker compose down
```

### Running Locally (Development)

For local development without Docker:

1. Install dependencies:
```bash
pip install -e ".[dev]"
```

2. Start Redis:
```bash
redis-server
```

3. Start the worker:
```bash
celery -A app.worker.celery_app worker --loglevel=info --concurrency=2
```

4. Start the API (in another terminal):
```bash
uvicorn app.main:app --reload
```

## Usage

### Automatic Task Enqueueing

When a file is uploaded via `/v1/uploads`, a parsing task is automatically enqueued:

```bash
curl -X POST http://localhost:8000/v1/uploads \
  -F "file=@config.tar.gz" \
  -F "type=ds_etc" \
  -F "label=My Config"
```

The response includes the run ID. The worker will process the file asynchronously.

### Monitoring Tasks

#### Check Worker Health

```bash
curl http://localhost:8000/v1/worker/health
```

Response:
```json
{
  "status": "healthy",
  "workers": 1,
  "active_tasks": 2,
  "worker_names": ["celery@worker-1"],
  "stats": { ... }
}
```

#### Check Task Status

```bash
curl http://localhost:8000/v1/worker/tasks/{task_id}
```

Response:
```json
{
  "task_id": "abc123...",
  "status": "SUCCESS",
  "ready": true,
  "successful": true,
  "result": {
    "run_id": 42,
    "status": "completed",
    "files_parsed": 15,
    "stanzas_created": 234,
    "duration_seconds": 12.5
  }
}
```

### Checking Run Status

Query the run status to see parsing progress:

```bash
curl http://localhost:8000/v1/runs/{run_id}
```

Status values:
- `pending`: Upload in progress
- `stored`: File stored, waiting for parsing
- `parsing`: Parsing in progress
- `complete`: Successfully parsed
- `failed`: Parsing failed

### Detailed Job Status

Get detailed job status including error details and metrics:

```bash
curl http://localhost:8000/v1/worker/runs/{run_id}/status
```

Response includes:
```json
{
  "id": 42,
  "status": "failed",
  "task_id": "abc-123-def",
  "retry_count": 3,
  "error_message": "Permanent error: Invalid archive format",
  "error_traceback": "Traceback (most recent call last)...",
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:30Z",
  "metrics": {
    "duration_seconds": 330,
    "retry_count": 3,
    "error_type": "permanent"
  }
}
```

### Worker Metrics

Get aggregated worker and job metrics:

```bash
curl http://localhost:8000/v1/worker/metrics
```

Response:
```json
{
  "status_counts": {
    "complete": 150,
    "failed": 5,
    "parsing": 2
  },
  "retry_stats": {
    "avg_retries": 0.3,
    "max_retries": 3
  },
  "avg_duration_seconds": 45.5,
  "recent_failures": [
    {
      "run_id": 42,
      "error_message": "Invalid archive format",
      "retry_count": 0,
      "completed_at": "2024-01-15T10:05:30Z"
    }
  ]
}
```

## Configuration

### Task Settings

Configured in `app/worker/celery_app.py`:

| Setting | Value | Description |
|---------|-------|-------------|
| `task_time_limit` | 3600s (1 hour) | Hard timeout for tasks |
| `task_soft_time_limit` | 3300s (55 min) | Soft timeout (raises exception) |
| `task_acks_late` | True | Acknowledge after completion |
| `task_reject_on_worker_lost` | True | Reject if worker crashes |
| `worker_prefetch_multiplier` | 1 | Process one task at a time |
| `worker_max_tasks_per_child` | 100 | Restart worker after 100 tasks |

### Retry Configuration

Parse task retry settings (configured in task decorator):

| Setting | Value | Description |
|---------|-------|-------------|
| `max_retries` | 3 | Maximum retry attempts |
| `Retry delay` | Exponential backoff | 60s, 180s, 600s (1min, 3min, 10min) |
| `autoretry_for` | Manual control | Errors classified as transient or permanent |

### Error Classification

The worker intelligently classifies errors:

**Permanent Errors** (no retry):
- Malformed or corrupted archives
- Unsupported archive formats
- Missing required data (no files found)
- Schema validation failures

**Transient Errors** (retry with backoff):
- Network connectivity issues
- Database connection errors
- Storage backend temporary failures
- Resource unavailability

### Retry Behavior

1. **Exponential Backoff**: Retries occur at 60s, 180s, and 600s intervals
2. **Error Tracking**: Each retry is logged with error details and stack traces
3. **Idempotency**: Tasks can be safely retried without creating duplicates
4. **Heartbeat**: Long-running tasks update heartbeat every 30 seconds
5. **Metrics**: Execution metrics collected on completion or failure

## Troubleshooting

### No Active Workers

**Symptom**: `/v1/worker/health` returns 503 error

**Solutions**:
1. Check if worker service is running:
   ```bash
   docker compose ps worker
   ```

2. Check worker logs:
   ```bash
   docker compose logs worker
   ```

3. Restart worker:
   ```bash
   docker compose restart worker
   ```

### Tasks Not Processing

**Symptom**: Runs stuck in `stored` status

**Solutions**:
1. Verify Redis connection:
   ```bash
   docker compose ps redis
   redis-cli -h localhost ping
   ```

2. Check for worker errors in logs:
   ```bash
   docker compose logs -f worker
   ```

3. Manually trigger a task (for testing):
   ```python
   from app.worker.tasks import parse_run
   task = parse_run.delay(run_id=1)
   print(f"Task ID: {task.id}")
   ```

### Parsing Failures

**Symptom**: Runs marked as `failed`

**Solutions**:
1. Check run details for error message:
   ```bash
   curl http://localhost:8000/v1/runs/{run_id}
   # Or use the detailed endpoint
   curl http://localhost:8000/v1/worker/runs/{run_id}/status
   ```

2. Review worker logs for stack traces:
   ```bash
   docker compose logs worker | grep ERROR
   ```

3. Common issues:
   - **Invalid archive format**: Only tar.gz, tar, zip supported (permanent error - won't retry)
   - **Corrupted archive**: File damaged during upload (permanent error - won't retry)
   - **Storage backend connectivity**: Network issues (transient - will retry)
   - **Database connection**: Temporary unavailability (transient - will retry)

### Understanding Error Types

The worker classifies errors into two categories:

**Permanent Errors** (will not retry):
- Error message starts with "Permanent error:"
- Common causes:
  - Malformed or corrupted archive files
  - Unsupported archive formats
  - Missing required data
  - Invalid configuration structure
- Action: Fix the input data and re-upload

**Transient Errors** (will retry with backoff):
- Error message starts with "Transient error (retry X):"
- Common causes:
  - Network connectivity issues
  - Database connection timeouts
  - Storage backend temporary failures
- Action: Monitor retry attempts; most resolve automatically

### Retry Exhaustion

**Symptom**: Run failed after 3 retries

**Error message**: "Failed after 3 retries: [error details]"

**Solutions**:
1. Check error details in run status:
   ```bash
   curl http://localhost:8000/v1/worker/runs/{run_id}/status
   ```

2. Common causes:
   - Persistent network issues
   - Database overload
   - Storage backend issues

3. Actions:
   - Fix underlying infrastructure issue
   - Re-upload the file to create a new run

### Task Timeouts

**Symptom**: Task fails with "Task exceeded time limit"

**Solutions**:
1. Check task duration in metrics:
   ```bash
   curl http://localhost:8000/v1/worker/metrics
   ```

2. For large archives:
   - Increase `task_time_limit` in `celery_app.py`
   - Split large archives into smaller bundles
   - Check for performance bottlenecks in logs

### Monitoring Task Progress

**Check heartbeat for long-running tasks**:
```bash
curl http://localhost:8000/v1/worker/runs/{run_id}/status | jq '.last_heartbeat'
```

If `last_heartbeat` hasn't updated in >2 minutes, the task may be stuck.

### High Memory Usage

**Symptom**: Worker using excessive memory

**Solutions**:
1. Reduce worker concurrency:
   ```bash
   celery -A app.worker.celery_app worker --loglevel=info --concurrency=1
   ```

2. Adjust `worker_max_tasks_per_child` to restart workers more frequently

3. Monitor task execution times and optimize parsing logic

### Database Connection Issues

**Symptom**: Frequent database errors in logs

**Error pattern**: "Database error: [connection details]"

**Solutions**:
1. Check database connection pool settings
2. Verify database is accessible from worker container
3. Check database server load and performance
4. Review `task_acks_late` setting - ensures tasks re-queue on connection loss

## Monitoring and Observability

### Logs

Worker logs include structured information:
- Task start/completion
- Parsing progress (files and stanzas)
- Error details with stack traces
- Task duration and performance metrics
- Retry attempts and backoff timing
- Heartbeat updates for long-running tasks

### Metrics

Key metrics to monitor (available via `/v1/worker/metrics` endpoint):

- **Job Status Counts**: Number of jobs in each status
- **Retry Statistics**: Average and maximum retry counts
- **Success/Failure Rate**: Percentage of successful completions
- **Average Duration**: Mean execution time for completed jobs
- **Recent Failures**: List of recent failed jobs with error details

### Error Tracking

Each job stores comprehensive error information:
- `error_message`: High-level error description
- `error_traceback`: Full Python traceback for debugging
- `retry_count`: Number of retry attempts
- `metrics.error_type`: Classification (permanent, transient, timeout, etc.)

### Task Monitoring Fields

The `IngestionRun` model tracks:
- `task_id`: Celery task ID for correlation
- `started_at`: When task execution began
- `last_heartbeat`: Last activity timestamp (for timeout detection)
- `completed_at`: When task finished (success or failure)
- `metrics`: JSON object with execution metrics

### Alerting Recommendations

Set up alerts for:
1. **High failure rate**: >10% of jobs failing
2. **Retry exhaustion**: Jobs consistently hitting max retries
3. **Long-running tasks**: Tasks with stale heartbeats (>5 minutes)
4. **Worker unavailability**: No active workers detected
5. **Queue backlog**: High number of pending jobs

### Celery Flower (Optional)

For advanced monitoring, install Celery Flower:

```bash
pip install flower
flower -A app.worker.celery_app --port=5555
```

Access at `http://localhost:5555` for:
- Real-time task monitoring
- Worker status and statistics
- Task history and performance graphs

## Best Practices

1. **Monitor Worker Health**: Regularly check `/v1/worker/health` endpoint
2. **Scale Workers**: Add more workers for high-volume workloads
3. **Set Resource Limits**: Use Docker resource constraints for workers
4. **Review Logs**: Monitor worker logs for errors and performance issues
5. **Test Retries**: Ensure retry logic works for transient failures
6. **Backup Redis**: Consider Redis persistence for task queue durability

## Integration with CI/CD

The worker service is included in CI tests:

```bash
# Run integration tests
docker compose up -d
pytest backend/tests/test_worker_integration.py
docker compose down
```

## Advanced Configuration

### Multiple Worker Pools

Run workers with different queues for priority processing:

```bash
# High-priority worker
celery -A app.worker.celery_app worker -Q high_priority --concurrency=4

# Low-priority worker
celery -A app.worker.celery_app worker -Q low_priority --concurrency=2
```

### Custom Task Routing

Configure task routing in `celery_app.py`:

```python
celery_app.conf.task_routes = {
    'app.worker.tasks.parse_run': {'queue': 'parsing'},
}
```

## Security Considerations

1. **Redis Security**: Use Redis AUTH and TLS in production
2. **Task Validation**: Validate run_id before processing
3. **Resource Limits**: Set memory and CPU limits for workers
4. **Timeouts**: Configure appropriate task timeouts
5. **Error Handling**: Don't expose sensitive information in error messages

## Support

For issues or questions:
- Check worker logs: `docker compose logs worker`
- Review run status: `GET /v1/runs/{run_id}`
- Check worker health: `GET /v1/worker/health`
- Open an issue on GitHub with logs and error details

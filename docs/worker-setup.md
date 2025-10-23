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

Parse task retry settings:

| Setting | Value | Description |
|---------|-------|-------------|
| `max_retries` | 3 | Maximum retry attempts |
| `default_retry_delay` | 60s | Base retry delay |
| `retry_backoff` | True | Exponential backoff |
| `retry_backoff_max` | 600s (10 min) | Maximum delay between retries |
| `retry_jitter` | True | Add randomness to prevent thundering herd |

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
   ```

2. Review worker logs for stack traces:
   ```bash
   docker compose logs worker | grep ERROR
   ```

3. Common issues:
   - Invalid archive format (only tar.gz, tar, zip supported)
   - Corrupted archive file
   - Storage backend connectivity issues
   - Database connection issues

### High Memory Usage

**Symptom**: Worker using excessive memory

**Solutions**:
1. Reduce worker concurrency:
   ```bash
   celery -A app.worker.celery_app worker --loglevel=info --concurrency=1
   ```

2. Adjust `worker_max_tasks_per_child` to restart workers more frequently

3. Monitor task execution times and optimize parsing logic

## Monitoring and Observability

### Logs

Worker logs include structured information:
- Task start/completion
- Parsing progress (files and stanzas)
- Error details with stack traces
- Task duration and performance metrics

### Metrics

Key metrics to monitor:
- **Worker count**: Number of active workers
- **Active tasks**: Currently executing tasks
- **Task duration**: Time to complete parsing
- **Success/failure rate**: Task outcome statistics
- **Retry count**: Number of task retries

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

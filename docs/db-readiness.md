# Database Readiness & Wait Strategy

## Overview

This document describes the database readiness/wait strategy implementation for Splunk Auto Doc. The strategy ensures that database connections are established and verified before the application starts or migrations run, preventing race conditions in both local development and CI environments.

## Problem Statement

Docker Compose health checks provide basic container readiness, but race conditions can still occur when:
- FastAPI starts before PostgreSQL is ready to accept connections
- Alembic migrations run before the database schema is initialized
- CI tests start before the database service is fully operational

These race conditions lead to:
- Connection errors during application startup
- Failed migrations in CI workflows
- Inconsistent developer experience requiring manual retries
- Unclear error messages for debugging

## Solution Architecture

### Components

1. **Python Wait Script** (`backend/scripts/wait_for_db.py`)
   - Primary wait mechanism for local and CI environments
   - Uses SQLAlchemy to verify database connectivity
   - Configurable retry logic with environment variables
   - Clear error messages and troubleshooting guidance

2. **Shell Wait Script** (`backend/scripts/wait-for-db.sh`)
   - Alternative wait mechanism using PostgreSQL client tools
   - Useful for environments where Python dependencies aren't available yet
   - Uses `pg_isready` and `psql` for verification

3. **Health Check Endpoints** (`/health/ready`, `/v1/ready`)
   - Runtime database connectivity verification
   - Returns HTTP 200 if database is healthy, 503 if not
   - Used for container orchestration and monitoring

4. **Docker Compose Integration**
   - API service automatically waits for database before starting
   - Runs migrations after database is ready
   - Proper service dependency ordering with health checks

5. **CI Integration** (`.github/workflows/backend-ci.yml`)
   - PostgreSQL service with health checks
   - Explicit wait step before migrations
   - Database verification before running tests

## Usage

### Docker Compose (Recommended for Local Development)

The simplest way to use the database readiness strategy:

```bash
# Start all services - database wait is automatic
docker compose up -d

# View logs to see the wait process
docker compose logs -f api
```

The API container will:
1. Wait for the database to be ready (up to 60 seconds by default)
2. Run Alembic migrations
3. Start the FastAPI application

### Manual Wait (Local Development)

For custom setups or debugging:

```bash
# Using Python script (recommended)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/splunk_auto_doc"
python backend/scripts/wait_for_db.py

# With custom retry settings
python backend/scripts/wait_for_db.py --max-retries 60 --retry-interval 1

# Using shell script (requires PostgreSQL client)
export DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_NAME=splunk_auto_doc
bash backend/scripts/wait-for-db.sh

# Using Makefile target
make wait-for-db
```

### CI/CD Integration

The CI workflow automatically handles database readiness:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

steps:
  - name: Wait for PostgreSQL
    run: python backend/scripts/wait_for_db.py --max-retries 10 --retry-interval 3

  - name: Run database migrations
    run: cd backend && alembic upgrade head

  - name: Run tests
    run: pytest backend/tests/
```

### Health Check Endpoints

Check database connectivity at runtime:

```bash
# Legacy endpoint
curl http://localhost:8000/health/ready

# V1 API endpoint
curl http://localhost:8000/v1/ready
```

Response when ready (HTTP 200):
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy"
  }
}
```

Response when not ready (HTTP 503):
```json
{
  "status": "not ready",
  "checks": {
    "database": "unhealthy: could not connect to server..."
  }
}
```

## Configuration

### Environment Variables

**Python Script (`wait_for_db.py`):**
- `DATABASE_URL` - Full PostgreSQL connection string (required)
- `DB_MAX_RETRIES` - Maximum retry attempts (default: 30)
- `DB_RETRY_INTERVAL` - Seconds between retries (default: 2)

**Shell Script (`wait-for-db.sh`):**
- `DB_HOST` - PostgreSQL hostname (default: db)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_USER` - PostgreSQL username (default: postgres)
- `DB_PASSWORD` - PostgreSQL password (default: postgres)
- `DB_NAME` - Database name (default: splunk_auto_doc)
- `DB_MAX_RETRIES` - Maximum retry attempts (default: 30)
- `DB_RETRY_INTERVAL` - Seconds between retries (default: 2)

### Docker Compose Configuration

The `docker-compose.yml` includes:

```yaml
api:
  environment:
    - DATABASE_URL=postgresql://postgres:postgres@db:5432/splunk_auto_doc
    - DB_HOST=db
    - DB_PORT=5432
    # ... other variables
  depends_on:
    db:
      condition: service_healthy
  command: >
    sh -c "python scripts/wait_for_db.py &&
           alembic upgrade head &&
           uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

## Troubleshooting

### Database Connection Failures

If the wait script times out:

1. **Check PostgreSQL is running:**
   ```bash
   docker compose ps db
   # Should show "healthy" status
   ```

2. **Check database logs:**
   ```bash
   docker compose logs db
   # Look for startup errors or connection issues
   ```

3. **Verify environment variables:**
   ```bash
   docker compose exec api env | grep DATABASE_URL
   # Should show correct connection string
   ```

4. **Test connection manually:**
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   # Should connect and return result
   ```

5. **Check health check status:**
   ```bash
   curl http://localhost:8000/health/ready
   # Should return 200 OK with database: healthy
   ```

### Common Issues

**"psql: command not found" in shell script:**
- Solution: Use Python script instead, or install PostgreSQL client tools

**"ModuleNotFoundError: No module named 'sqlalchemy'" in Python script:**
- Solution: Install dependencies: `pip install -e ".[dev]"`

**Wait script succeeds but application fails to start:**
- Check application logs: `docker compose logs api`
- Verify migrations completed: `docker compose exec api alembic current`
- Check for application-specific errors unrelated to database

**CI tests fail with database connection errors:**
- Verify PostgreSQL service is configured with health checks
- Ensure wait step runs before migrations and tests
- Check DATABASE_URL environment variable in workflow

### Adjusting Timeouts

For slow environments (e.g., limited CI resources):

```bash
# Increase retries and interval
export DB_MAX_RETRIES=60
export DB_RETRY_INTERVAL=3
python backend/scripts/wait_for_db.py
```

For fast environments (e.g., local development):

```bash
# Decrease retries and interval
export DB_MAX_RETRIES=10
export DB_RETRY_INTERVAL=1
python backend/scripts/wait_for_db.py
```

## Testing

The implementation includes comprehensive tests in `backend/tests/test_db_readiness.py`:

- Basic health check always returns healthy
- Readiness check verifies database connectivity
- Readiness check returns 503 when database is unavailable
- Tests for both legacy and v1 API endpoints

Run tests:
```bash
pytest backend/tests/test_db_readiness.py -v
```

## Best Practices

1. **Always use the wait scripts in production-like environments**
   - Docker Compose should include wait + migrate + start sequence
   - CI should wait before migrations and tests

2. **Monitor readiness endpoints**
   - Use `/health/ready` for container orchestration health checks
   - Monitor for 503 responses indicating database issues

3. **Set appropriate timeouts**
   - Local development: 30-60 seconds is usually sufficient
   - CI environments: May need 60-120 seconds depending on resources
   - Production: Use shorter timeouts (10-20s) with proper monitoring

4. **Log database readiness checks**
   - Scripts provide clear output for debugging
   - Check logs if experiencing connection issues

5. **Use health checks in orchestration**
   - Docker Compose: Use `condition: service_healthy`
   - Kubernetes: Use readiness probes with `/health/ready`
   - Load balancers: Check `/health/ready` before routing traffic

## References

- Issue: [#41 - Implement DB Readiness/Wait Strategy](https://github.com/Alrudin/Splunk_auto_doc/issues/41)
- Milestone: Milestone 1 - Foundation Implementation
- Related: Docker Compose health checks, Alembic migrations, FastAPI lifespan

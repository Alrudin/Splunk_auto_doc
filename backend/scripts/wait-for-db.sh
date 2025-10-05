#!/bin/bash
# wait-for-db.sh - Wait for PostgreSQL database to be ready
# This script ensures the database is ready before starting the application
# or running migrations, preventing race conditions in local and CI environments.

set -e

# Configuration from environment or defaults
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-splunk_auto_doc}"
MAX_RETRIES="${DB_MAX_RETRIES:-30}"
RETRY_INTERVAL="${DB_RETRY_INTERVAL:-2}"

echo "🔍 Waiting for PostgreSQL database to be ready..."
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   Max retries: $MAX_RETRIES"
echo "   Retry interval: ${RETRY_INTERVAL}s"
echo ""

# Function to check if PostgreSQL is ready
check_postgres() {
    pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q
    return $?
}

# Retry loop
retry_count=0
while [ $retry_count -lt $MAX_RETRIES ]; do
    retry_count=$((retry_count + 1))
    
    if check_postgres; then
        echo "✅ PostgreSQL is ready! (attempt $retry_count/$MAX_RETRIES)"
        
        # Additional verification: try to connect and run a simple query
        if PGPASSWORD="${DB_PASSWORD:-postgres}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
            echo "✅ Database connection verified"
            exit 0
        else
            echo "⚠️  pg_isready succeeded but connection test failed, retrying..."
        fi
    else
        echo "⏳ Waiting for PostgreSQL... (attempt $retry_count/$MAX_RETRIES)"
    fi
    
    if [ $retry_count -lt $MAX_RETRIES ]; then
        sleep $RETRY_INTERVAL
    fi
done

echo ""
echo "❌ ERROR: PostgreSQL did not become ready within $(($MAX_RETRIES * $RETRY_INTERVAL)) seconds"
echo ""
echo "Troubleshooting steps:"
echo "  1. Check if PostgreSQL container is running: docker compose ps db"
echo "  2. Check PostgreSQL logs: docker compose logs db"
echo "  3. Verify DATABASE_URL environment variable is correct"
echo "  4. Ensure PostgreSQL health check is configured in docker-compose.yml"
echo ""
exit 1

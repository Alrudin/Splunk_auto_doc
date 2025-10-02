#!/bin/bash
# Helper script to run database migrations

set -e

cd "$(dirname "$0")/.."

echo "Running Alembic migrations..."
alembic upgrade head

echo ""
echo "Migration complete! Current version:"
alembic current

echo ""
echo "Database tables:"
alembic show head

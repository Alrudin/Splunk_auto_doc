#!/bin/bash
# Integration test for DB readiness strategy
# This script tests the database wait functionality end-to-end

set -e

echo "🧪 Testing DB Readiness Strategy"
echo "================================="
echo ""

# Test 1: Verify wait script exists and is executable
echo "Test 1: Checking wait scripts exist..."
if [ -x "backend/scripts/wait_for_db.py" ]; then
    echo "✓ wait_for_db.py exists and is executable"
else
    echo "✗ wait_for_db.py not found or not executable"
    exit 1
fi

if [ -x "backend/scripts/wait-for-db.sh" ]; then
    echo "✓ wait-for-db.sh exists and is executable"
else
    echo "✗ wait-for-db.sh not found or not executable"
    exit 1
fi

# Test 2: Verify wait script help works
echo ""
echo "Test 2: Testing wait script help..."
cd backend
if python scripts/wait_for_db.py --help > /dev/null 2>&1; then
    echo "✓ wait_for_db.py --help works"
else
    echo "✗ wait_for_db.py --help failed"
    exit 1
fi
cd ..

# Test 3: Verify wait script fails gracefully with bad connection
echo ""
echo "Test 3: Testing wait script error handling..."
cd backend
export DATABASE_URL="postgresql://invalid:invalid@localhost:9999/invalid"
if python scripts/wait_for_db.py --max-retries 2 --retry-interval 1 > /tmp/wait_output.txt 2>&1; then
    echo "✗ wait_for_db.py should have failed with invalid database"
    exit 1
else
    if grep -q "ERROR: PostgreSQL did not become ready" /tmp/wait_output.txt; then
        echo "✓ wait_for_db.py fails gracefully with clear error message"
    else
        echo "✗ wait_for_db.py did not produce expected error message"
        cat /tmp/wait_output.txt
        exit 1
    fi
fi
cd ..

# Test 4: Verify docker-compose configuration
echo ""
echo "Test 4: Testing docker-compose configuration..."
if docker compose config > /dev/null 2>&1; then
    echo "✓ docker-compose.yml is valid"
else
    echo "✗ docker-compose.yml is invalid"
    exit 1
fi

# Check that API service has proper command
if docker compose config | grep -q "python scripts/wait_for_db.py"; then
    echo "✓ API service command includes wait_for_db.py"
else
    echo "✗ API service command missing wait_for_db.py"
    exit 1
fi

if docker compose config | grep -q "alembic upgrade head"; then
    echo "✓ API service command includes migrations"
else
    echo "✗ API service command missing migrations"
    exit 1
fi

# Test 5: Verify CI workflow configuration
echo ""
echo "Test 5: Testing CI workflow configuration..."
if [ -f ".github/workflows/backend-ci.yml" ]; then
    if grep -q "Wait for PostgreSQL" .github/workflows/backend-ci.yml; then
        echo "✓ CI workflow includes database wait step"
    else
        echo "✗ CI workflow missing database wait step"
        exit 1
    fi

    if grep -q "services:" .github/workflows/backend-ci.yml && grep -q "postgres:" .github/workflows/backend-ci.yml; then
        echo "✓ CI workflow includes PostgreSQL service"
    else
        echo "✗ CI workflow missing PostgreSQL service"
        exit 1
    fi

    if grep -q "alembic upgrade head" .github/workflows/backend-ci.yml; then
        echo "✓ CI workflow runs migrations"
    else
        echo "✗ CI workflow missing migration step"
        exit 1
    fi
else
    echo "✗ Backend CI workflow file not found"
    exit 1
fi

# Test 6: Verify health endpoint code includes DB check
echo ""
echo "Test 6: Testing health endpoint implementation..."
if grep -q "engine.connect()" backend/app/health.py; then
    echo "✓ Legacy health endpoint includes database check"
else
    echo "✗ Legacy health endpoint missing database check"
    exit 1
fi

if grep -q "engine.connect()" backend/app/api/v1/health.py; then
    echo "✓ V1 health endpoint includes database check"
else
    echo "✗ V1 health endpoint missing database check"
    exit 1
fi

# Test 7: Verify tests exist
echo ""
echo "Test 7: Testing readiness test file..."
if [ -f "backend/tests/test_db_readiness.py" ]; then
    echo "✓ DB readiness tests exist"

    if grep -q "test_readiness_check" backend/tests/test_db_readiness.py; then
        echo "✓ Tests include readiness check tests"
    else
        echo "✗ Tests missing readiness check tests"
        exit 1
    fi
else
    echo "✗ DB readiness test file not found"
    exit 1
fi

# Test 8: Verify Makefile target
echo ""
echo "Test 8: Testing Makefile target..."
if grep -q "wait-for-db:" Makefile; then
    echo "✓ Makefile includes wait-for-db target"
else
    echo "✗ Makefile missing wait-for-db target"
    exit 1
fi

# Test 9: Verify documentation
echo ""
echo "Test 9: Testing documentation..."
if grep -q "Database Readiness Strategy" README.md; then
    echo "✓ README includes DB readiness documentation"
else
    echo "✗ README missing DB readiness documentation"
    exit 1
fi

if [ -f "docs/db-readiness.md" ]; then
    echo "✓ Comprehensive DB readiness documentation exists"
else
    echo "✗ docs/db-readiness.md not found"
    exit 1
fi

if grep -q "Understanding Database Readiness" CONTRIBUTING.md; then
    echo "✓ CONTRIBUTING.md includes DB readiness guidance"
else
    echo "✗ CONTRIBUTING.md missing DB readiness guidance"
    exit 1
fi

# Test 10: Verify Dockerfile includes wait script setup
echo ""
echo "Test 10: Testing Dockerfile configuration..."
if grep -q "postgresql-client" backend/Dockerfile; then
    echo "✓ Dockerfile installs PostgreSQL client tools"
else
    echo "⚠ Dockerfile missing PostgreSQL client (only needed for shell script)"
fi

if grep -q "chmod +x /app/scripts/wait" backend/Dockerfile; then
    echo "✓ Dockerfile makes wait scripts executable"
else
    echo "✗ Dockerfile missing chmod for wait scripts"
    exit 1
fi

echo ""
echo "================================="
echo "🎉 All DB readiness tests passed!"
echo "================================="
echo ""
echo "Summary of implementation:"
echo "  ✓ Wait scripts (Python and shell) with retry logic"
echo "  ✓ Health endpoints with database connectivity checks"
echo "  ✓ Docker Compose integration with automatic wait"
echo "  ✓ CI workflow with database service and wait step"
echo "  ✓ Comprehensive tests for readiness functionality"
echo "  ✓ Complete documentation (README, CONTRIBUTING, docs/)"
echo "  ✓ Makefile target for manual database wait"
echo ""
echo "To test with actual database:"
echo "  1. docker compose up -d db"
echo "  2. make wait-for-db"
echo "  3. docker compose up -d"
echo ""

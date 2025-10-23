#!/bin/bash
# Quick validation script for worker service setup

echo "=== Worker Service Validation ==="
echo ""

echo "1. Checking file structure..."
if [ -f "backend/app/worker/celery_app.py" ]; then
    echo "   ✓ celery_app.py exists"
else
    echo "   ✗ celery_app.py missing"
    exit 1
fi

if [ -f "backend/app/worker/tasks.py" ]; then
    echo "   ✓ tasks.py exists"
else
    echo "   ✗ tasks.py missing"
    exit 1
fi

if [ -f "backend/app/api/v1/worker.py" ]; then
    echo "   ✓ worker.py (health endpoint) exists"
else
    echo "   ✗ worker.py missing"
    exit 1
fi

echo ""
echo "2. Checking Python syntax..."
python -m py_compile backend/app/worker/*.py backend/app/api/v1/worker.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ Python syntax valid"
else
    echo "   ✗ Python syntax errors"
    exit 1
fi

echo ""
echo "3. Checking docker-compose configuration..."
if grep -q "worker:" docker-compose.yml; then
    echo "   ✓ Worker service defined in docker-compose.yml"
else
    echo "   ✗ Worker service not found in docker-compose.yml"
    exit 1
fi

if grep -q "celery -A app.worker.celery_app worker" docker-compose.yml; then
    echo "   ✓ Celery worker command configured"
else
    echo "   ✗ Celery worker command not found"
    exit 1
fi

echo ""
echo "4. Checking dependencies..."
if grep -q "celery" pyproject.toml; then
    echo "   ✓ Celery dependency added"
else
    echo "   ✗ Celery dependency missing"
    exit 1
fi

if grep -q "redis" pyproject.toml; then
    echo "   ✓ Redis dependency added"
else
    echo "   ✗ Redis dependency missing"
    exit 1
fi

echo ""
echo "5. Checking documentation..."
if [ -f "docs/worker-setup.md" ]; then
    echo "   ✓ Worker documentation exists"
else
    echo "   ✗ Worker documentation missing"
    exit 1
fi

echo ""
echo "6. Checking tests..."
if [ -f "backend/tests/test_worker_integration.py" ]; then
    echo "   ✓ Integration tests exist"
else
    echo "   ✗ Integration tests missing"
    exit 1
fi

echo ""
echo "=== Validation Complete ==="
echo "All checks passed! ✓"
echo ""
echo "To run the worker service:"
echo "  docker compose up -d"
echo ""
echo "To check worker health:"
echo "  curl http://localhost:8000/v1/worker/health"

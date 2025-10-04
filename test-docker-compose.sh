#!/bin/bash

# Test script to validate Docker Compose configuration
# This script helps verify that all services are properly configured

set -e

echo "🧪 Testing Docker Compose Configuration for Splunk Auto Doc"
echo "============================================================="

# Check if docker compose is available
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not available"
    exit 1
fi

# Validate docker-compose.yml syntax
echo "✅ Validating docker-compose.yml syntax..."
docker compose config > /dev/null
echo "✅ Docker Compose configuration is valid"

# Check required files exist
echo "✅ Checking required files..."
required_files=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "nginx.conf"
    "frontend/index.html"
    ".env.example"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        exit 1
    fi
done

# Check directories
echo "✅ Checking required directories..."
required_dirs=(
    "backend"
    "frontend"
    "storage"
)

for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        echo "✅ $dir directory exists"
    else
        echo "❌ $dir directory is missing"
        exit 1
    fi
done

# Validate service configuration
echo "✅ Validating service configuration..."
services=("api" "db" "minio" "redis" "frontend")
for service in "${services[@]}"; do
    if docker compose config --services | grep -q "^$service$"; then
        echo "✅ Service '$service' is configured"
    else
        echo "❌ Service '$service' is missing from configuration"
        exit 1
    fi
done

# Check network configuration
if docker compose config | grep -q "app-network"; then
    echo "✅ Custom network 'app-network' is configured"
else
    echo "❌ Custom network 'app-network' is missing"
    exit 1
fi

# Check volumes
volumes=("postgres_data" "minio_data" "redis_data")
for volume in "${volumes[@]}"; do
    if docker compose config | grep -q "$volume"; then
        echo "✅ Volume '$volume' is configured"
    else
        echo "❌ Volume '$volume' is missing"
        exit 1
    fi
done

echo ""
echo "🎉 All Docker Compose configuration tests passed!"
echo ""
echo "📋 Services configured:"
echo "   • API (FastAPI backend) - http://localhost:8000"
echo "   • Database (PostgreSQL) - localhost:5432"
echo "   • MinIO (Object Storage) - http://localhost:9000 (console: http://localhost:9001)"
echo "   • Redis (Cache) - localhost:6379"
echo "   • Frontend (Nginx placeholder) - http://localhost:3000"
echo ""
echo "🚀 To start all services: docker compose up -d"
echo "🛑 To stop all services: docker compose down"
echo "📊 To view logs: docker compose logs -f"

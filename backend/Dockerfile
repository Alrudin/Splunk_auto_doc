FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client for wait-for-db script
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml /app/
COPY README.md /app/

# Copy application code directly to /app (flattening the structure)
COPY backend/ /app/

# Fix pyproject.toml paths for the flattened structure
RUN sed -i 's|backend/app/__init__.py|app/__init__.py|g' /app/pyproject.toml && \
    sed -i 's|"backend/app"|"app"|g' /app/pyproject.toml

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Create storage directory
RUN mkdir -p /app/storage

# Make scripts executable
RUN chmod +x /app/scripts/wait-for-db.sh /app/scripts/wait_for_db.py

# Expose port
EXPOSE 8000

# Run the application (wait-for-db will be called via docker-compose command)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

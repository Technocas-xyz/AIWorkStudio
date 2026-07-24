#!/bin/bash
set -e

echo "=== AI Work Studio - Starting ==="

# Wait for database to be ready
echo "Waiting for database..."
until pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-aws_user} 2>/dev/null; do
  echo "  Database not ready, waiting..."
  sleep 2
done
echo "✓ Database is ready!"

# Create upload directories
mkdir -p /app/app/uploads/originals /app/app/uploads/previews /app/app/uploads/versions /app/app/uploads/generations
echo "✓ Upload directories ready"

# Start the application (auto-seed happens in lifespan)
echo "Starting AI Work Studio API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

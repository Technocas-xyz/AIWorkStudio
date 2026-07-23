#!/bin/bash
# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  sleep 1
done
echo "Database is ready!"

# Run migrations
echo "Running migrations..."
cd /app && alembic upgrade head

# Seed initial data
echo "Seeding database..."
python -m app.database.seed

# Start the application
echo "Starting AI Work Studio API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

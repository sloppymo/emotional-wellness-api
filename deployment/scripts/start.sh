#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.5
done
echo "Database is up!"

# Apply migrations if needed
if [ "$APPLY_MIGRATIONS" = "true" ]; then
  echo "Applying database migrations..."
  # In production, you'd use alembic or another migration tool here
  # For now, we'll just placeholder this step
  sleep 1
  echo "Migrations applied successfully"
fi

# Start the application with Gunicorn for production workloads
if [ "$ENVIRONMENT" = "production" ]; then
  echo "Starting API in production mode..."
  exec gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --log-level=info \
    --access-logfile - \
    --error-logfile -
else
  # Start with Uvicorn for development
  echo "Starting API in development mode..."
  exec uvicorn src.main:app --host 0.0.0.0 --port $PORT --reload
fi

#!/usr/bin/env bash
set -e

echo "=== Starting CineSense Production Container ==="

APP_PORT="${PORT:-8000}"

# Run Alembic migrations if DATABASE_URL is configured
if [ -n "$DATABASE_URL" ]; then
    echo "Configuring database connection..."
    if [ -f "alembic.ini" ]; then
        echo "Running database migrations (alembic upgrade head)..."
        # Retry up to 5 times with a 2-second sleep to allow Postgres to initialize
        for i in {1..5}; do
            if uv run alembic upgrade head; then
                echo "Database migrations completed successfully."
                break
            fi
            echo "Alembic migration attempt $i/5 failed or database warming up. Retrying in 2s..."
            sleep 2
        done
    fi
fi

echo "Launching CineSense application on port $APP_PORT..."
exec uv run python -m uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"

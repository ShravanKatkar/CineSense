#!/usr/bin/env bash
set -e

echo "=== Starting CineSense Production Container ==="

# Wait for PostgreSQL database to be ready if DATABASE_URL is configured
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connection..."
    # Extract host and port if possible, or wait a few seconds
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's/.*@([^:]+).*/\1/' | sed -E 's/\/.*//')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's/.*:([0-9]+)\/.*/\1/')
    
    if [ -n "$DB_HOST" ] && command -v pg_isready >/dev/null 2>&1; then
        echo "Waiting for PostgreSQL at $DB_HOST:${DB_PORT:-5432}..."
        for i in {1..30}; do
            if pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" >/dev/null 2>&1; then
                echo "PostgreSQL is ready!"
                break
            fi
            echo "Waiting for PostgreSQL ($i/30)..."
            sleep 1
        done
    fi

    # Run Alembic migrations
    if [ -f "alembic.ini" ]; then
        echo "Running database migrations (alembic upgrade head)..."
        uv run alembic upgrade head || echo "Migration warning: tables may already exist or alembic reported no changes."
    fi
fi

echo "Launching CineSense application..."
exec "$@"

#!/bin/bash

# Exit on error
set -e

# Handle signals
trap 'kill -TERM $PID' TERM INT

# Check required environment variables
required_vars=("REDIS_HOST" "REDIS_PORT" "DJANGO_SECRET_KEY" "ALLOWED_HOSTS")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    for i in $(seq 1 30); do
        if nc -z "${REDIS_HOST}" "${REDIS_PORT}"; then
            echo "Redis is up"
            return 0
        fi
        echo "Redis is unavailable - retry $i/30"
        sleep 1
    done
    echo "Error: Redis did not become available in time"
    exit 1
}

echo "Running startup checks..."

# Check required environment variables
required_vars=(
    "REDIS_HOST" "REDIS_PORT"
    "POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_HOST"
)
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Wait for Redis
wait_for_redis

# Create necessary directories
mkdir -p /app/web/{staticfiles,media}
chmod -R 777 /app/web/{staticfiles,media}

cd /app || exit 1

# Run database migrations with retry
echo "Running database migrations..."
for i in $(seq 1 5); do
    if python web/manage.py migrate --noinput; then
        break
    fi
    if [ $i -eq 5 ]; then
        echo "Error: Database migrations failed after 5 attempts"
        exit 1
    fi
    echo "Migration attempt $i failed, retrying..."
    sleep 5
done

# Install Django REST framework static files
echo "Installing Django REST framework static files..."

# First collect all static files
python web/manage.py collectstatic --noinput --clear

# Then explicitly copy DRF static files
cp -r /usr/local/lib/python3.11/site-packages/rest_framework/static/rest_framework/* /app/web/staticfiles/rest_framework/

# Ensure proper ownership and permissions
chown -R web:web /app/web/staticfiles
chmod -R 755 /app/web/staticfiles

# Create cache table
echo "Creating cache table..."
if ! python web/manage.py createcachetable; then
    echo "Error: Failed to create cache table"
    exit 1
fi

echo "Starting Gunicorn..."
exec "$@"
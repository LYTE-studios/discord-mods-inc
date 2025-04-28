#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Function to handle environment file
setup_env() {
    # If .env file exists, copy it to a readable location
    if [ -f /app/.env ]; then
        cp /app/.env /app/.env.d/env
        chmod 600 /app/.env.d/env
        export $(cat /app/.env.d/env | xargs)
    fi
}

# Function to check Redis connection
redis_ready() {
    python << END
import sys
import redis
try:
    redis.Redis(
        host="${REDIS_HOST}",
        port=${REDIS_PORT},
        socket_connect_timeout=1,
    ).ping()
except redis.ConnectionError:
    sys.exit(-1)
sys.exit(0)
END
}

# Set up environment
setup_env

# Wait for Redis
until redis_ready; do
  >&2 echo "Waiting for Redis to become available..."
  sleep 1
done
>&2 echo "Redis is available"

# Ensure proper permissions
chmod -R 755 /app/static /app/media

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create cache table
python manage.py createcachetable

# Start server
exec "$@"
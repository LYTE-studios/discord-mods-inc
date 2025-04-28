#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

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

# Wait for Redis
until redis_ready; do
  >&2 echo "Waiting for Redis to become available..."
  sleep 1
done
>&2 echo "Redis is available"

# Ensure static directory exists with proper permissions
if [ ! -d "/app/static" ]; then
    # These commands run as root since the script is owned by root
    mkdir -p /app/static
    chown -R web:web /app/static
    chmod -R 777 /app/static
fi

# Switch to web user for Django commands
exec su web -c "
    # Apply database migrations
    python manage.py migrate --noinput

    # Collect static files
    python manage.py collectstatic --noinput

    # Create cache table
    python manage.py createcachetable

    # Execute the main command
    exec $*
"

# Start server
exec "$@"
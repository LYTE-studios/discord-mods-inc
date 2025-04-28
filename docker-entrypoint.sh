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

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create cache table
python manage.py createcachetable

# Start server
exec "$@"
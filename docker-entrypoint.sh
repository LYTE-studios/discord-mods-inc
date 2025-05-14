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

# Create and set permissions for static directories
mkdir -p /app/web/staticfiles /app/web/media /app/web/static
chown -R web:web /app/web/staticfiles /app/web/media /app/web/static
chmod -R 777 /app/web/staticfiles /app/web/media /app/web/static

# Run Django commands as web user
gosu web python manage.py migrate --noinput
gosu web python manage.py collectstatic --noinput
gosu web python manage.py createcachetable

# Execute the main command as web user
exec gosu web "$@"

# Note: Don't need the final exec "$@" as it's already handled by the previous exec
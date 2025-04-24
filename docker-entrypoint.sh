#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z "${REDIS_HOST}" "${REDIS_PORT}"; do
        sleep 0.1
    done
    echo "Redis is up!"
}

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# Wait for Redis if we're running the web server
if [ "${1}" = "gunicorn" ]; then
    wait_for_redis
fi

# Create cache table
python manage.py createcachetable --noinput

# Start Gunicorn
exec "$@"
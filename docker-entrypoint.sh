#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

postgres_ready() {
    python << END
import sys
import psycopg2
try:
    psycopg2.connect(
        dbname="gideon",
        user="postgres",
        password="0~cySne?(Ts4a~qD_)nLC:8?qKcZ",
        host="framer-api.cd4qc66im6mq.eu-central-1.rds.amazonaws.com",
        port="5432",
        options="-c target_session_attrs=read-write"
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

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

until postgres_ready; do
  >&2 echo "Waiting for RDS PostgreSQL to become available..."
  sleep 1
done
>&2 echo "RDS PostgreSQL is available"

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
python manage.py createcachetable --noinput

# Start server
exec "$@"
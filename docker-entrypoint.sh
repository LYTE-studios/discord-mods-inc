#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create cache table
python manage.py createcachetable --noinput

# Start server
exec "$@"
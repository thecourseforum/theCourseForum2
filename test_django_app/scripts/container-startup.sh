#!/bin/bash
set -e

echo "Container starting..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files to S3
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Clear expired sessions
echo "Clearing expired sessions..."
python manage.py clearsessions

echo "Starting Django server..."
exec gunicorn tcf_core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --log-level info \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

#!/bin/bash
set -e

echo "Loading grades w/ custom script [DELETE AFTR USE]"

python manage.py load_grades ALL_DANGEROUS

echo "Starting Django Server with Gunicorn..."

# Optimize workers and threads for your container's CPU allocation
exec gunicorn tcf_core.wsgi:application \
    --bind 0.0.0.0:80 \
    --workers 3 \
    --threads 2 \
    --log-level "info" \
    --timeout 120

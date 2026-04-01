#!/bin/bash
set -e

echo "Starting Django Server with Gunicorn..."

# Optimize workers and threads for your container's CPU allocation
exec gunicorn tcf_core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --log-level "info" \
    --timeout 120

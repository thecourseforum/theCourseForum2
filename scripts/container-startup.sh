#!/bin/bash
set -e

echo 'container running'

uv run manage.py migrate
echo 'migrate ran'

uv run manage.py collectstatic --noinput
echo 'collectstatic ran'

uv run manage.py invalidate_cachalot tcf_website

uv run manage.py clearsessions

# Add custom commands here
# python manage.py load_semester 2026_spring 

echo 'Starting Django Server...'
exec gunicorn tcf_core.wsgi:application --bind 0.0.0.0:80 --log-level "info" --timeout 120

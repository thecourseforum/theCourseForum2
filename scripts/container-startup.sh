#!/bin/bash
set -e

echo 'container running'

python manage.py migrate
echo 'migrate ran'

python manage.py collectstatic --noinput
echo 'collectstatic ran'

python manage.py invalidate_cachalot tcf_website

python manage.py clearsessions

# Add custom commands here

python manage.py generate_ai_summaries --semester 2026_fall --missing-only --model "arcee-ai/trinity-large-preview:free"

echo 'Starting Django Server...'
exec gunicorn tcf_core.wsgi:application --bind 0.0.0.0:80 --log-level "info" --timeout 120

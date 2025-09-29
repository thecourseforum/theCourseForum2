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

echo 'Starting Django Server...'
exec gunicorn tcf_core.wsgi:application --bind 0.0.0.0:80

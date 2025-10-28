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

echo 'Starting Django Server...'
uv run manage.py runserver 0.0.0.0:80 

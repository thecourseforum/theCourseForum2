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

# Run a small AI reviews summary batch after startup so summary generation doesn't not block health checks.
if [ -n "${OPENROUTER_API_KEY:-}" ] && [ "${AI_SUMMARY_STARTUP_LIMIT:-5}" -gt 0 ]; then
    (
        sleep "${AI_SUMMARY_STARTUP_DELAY_SECONDS:-30}"
        echo "Starting background AI summary generation..."

        summary_cmd=(
            python manage.py generate_ai_summaries
            --limit "${AI_SUMMARY_STARTUP_LIMIT:-5}"
            --min-reviews "${AI_SUMMARY_STARTUP_MIN_REVIEWS:-5}"
            --max-reviews "${AI_SUMMARY_STARTUP_MAX_REVIEWS:-12}"
            --missing-only # generate only new summaries
        )

        "${summary_cmd[@]}" || echo "Background AI summary generation failed."
    ) &
fi

echo 'Starting Django Server...'
exec gunicorn tcf_core.wsgi:application --bind 0.0.0.0:80 --log-level "info" --timeout 120

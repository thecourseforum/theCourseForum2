release: python manage.py collectstatic --noinput --clear && python manage.py makemigrations && cat tcf_website/migrations/* && python manage.py migrate
web: gunicorn tcf_core.wsgi --log-level debug

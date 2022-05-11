release: python manage.py collectstatic --noinput --clear && echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE" && python manage.py migrate
web: gunicorn tcf_core.wsgi --log-level debug

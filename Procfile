release: python manage.py collectstatic --noinput --clear && python manage.py makemigrations --verbosity 3 && echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE" && python manage.py migrate
web: gunicorn tcf_core.wsgi --log-level debug

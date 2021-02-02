release: python manage.py collectstatic --noinput --clear && python manage.py makemigrations -v 3 && echo $DJANGO_SETTINGS_MODULES; ls -a tcf_website && ls -a tcf_website/migrations; python manage.py migrate tcf_website
web: gunicorn tcf_core.wsgi --log-level debug

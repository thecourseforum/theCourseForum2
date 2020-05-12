release: python manage.py collectstatic --noinput --clear && python manage.py makemigrations tcf_website && python manage.py migrate
web: gunicorn tcf_core.wsgi

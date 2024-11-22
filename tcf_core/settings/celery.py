import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tcf_core.settings.base')

app = Celery('tcf_core')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

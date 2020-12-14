# pylint: disable=unused-wildcard-import,wildcard-import
"""Django settings module for production environment like Google App Engine"""
from .base import *

# The following if statement is needed to prevent overwriting global variables when
# this settings file is interpreted
if os.environ.get('DJANGO_SETTINGS_MODULE') == 'tcf_core.settings.prod':
    # SECURITY WARNING: App Engine's security features ensure that it is safe to
    # have ALLOWED_HOSTS = ['*'] when the app is deployed. If you deploy a Django
    # app not on App Engine, make sure to set an appropriate host here.
    # See https://docs.djangoproject.com/en/dev/ref/settings/ (from GCP
    # documentation)
    ALLOWED_HOSTS = ['*']

    # Use secure connection for database access
    DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}

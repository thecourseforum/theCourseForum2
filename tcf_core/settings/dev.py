# pylint: disable=import-error,unused-wildcard-import,wildcard-import
"""Django settings module for development environment such as Heroku"""

from .base import *

# The following if statement is needed to prevent overwriting global variables when
# this settings file is interpreted
if os.environ.get("DJANGO_SETTINGS_MODULE") == "tcf_core.settings.dev":
    # Use secure connection for database access
    DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

    # Configure Django App for Heroku.
    # This should be at the bottom
    # https://devcenter.heroku.com/articles/django-app-configuration
    # "This will automatically configure DATABASE_URL, ALLOWED_HOSTS, ... Logging"
    # https://github.com/heroku/django-heroku
    import django_heroku

    django_heroku.settings(locals(), databases=False)

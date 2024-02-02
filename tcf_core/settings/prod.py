# pylint: disable=unused-wildcard-import,wildcard-import
"""Django settings module for production environment like Google App Engine"""
from .base import *

# The following if statement is needed to prevent overwriting global variables when
# this settings file is interpreted
if os.environ.get("DJANGO_SETTINGS_MODULE") == "tcf_core.settings.prod":
    # SECURITY WARNING: App Engine's security features ensure that it is safe to
    # have ALLOWED_HOSTS = ['*'] when the app is deployed. If you deploy a Django
    # app not on App Engine, make sure to set an appropriate host here.
    # See https://docs.djangoproject.com/en/dev/ref/settings/ (from GCP
    # documentation)
    # Alex: "When I was trying to do manual GAE deployment when Travis was down,
    # I had to add thecourseforum.com to ALLOWED_HOSTS or the deployment wouldn't
    # work (see 40cac033ca14b5c379e5845f9c3870605cdac62d)."
    ALLOWED_HOSTS = ["*", "thecourseforum.com"]

    # Use secure connection for database access
    DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

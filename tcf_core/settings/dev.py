# pylint: disable=unused-wildcard-import,wildcard-import
"""Django settings for local development."""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".grok.io"]

# Local PostgreSQL database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DB_NAME"),
        "USER": env.str("DB_USER"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": env.str("DB_HOST"),
        "PORT": env.int("DB_PORT"),
    }
}

# Local static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(2, "debug_toolbar.middleware.DebugToolbarMiddleware")
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda r: True}

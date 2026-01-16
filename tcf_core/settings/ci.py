# pylint: disable=unused-wildcard-import,wildcard-import,duplicate-code
"""Django settings for CI (GitHub Actions)."""
from .base import *

# CI should mirror production: DEBUG=False catches issues early
DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# CI PostgreSQL database (GitHub Actions service container)
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

"""Django settings for local development and CI.

GitHub Actions sets GITHUB_ACTIONS=true on the runner; local shells do not.
"""

from .base import *

_ci = os.environ.get("GITHUB_ACTIONS") == "true"

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

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".grok.io", ".lhr.life"]


DEBUG = not _ci

if not _ci:
    INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
    MIDDLEWARE = (
        MIDDLEWARE[:2]
        + ["debug_toolbar.middleware.DebugToolbarMiddleware"]
        + MIDDLEWARE[2:]
    )
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda r: True}

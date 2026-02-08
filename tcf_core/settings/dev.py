# pylint: disable=unused-wildcard-import,wildcard-import,duplicate-code
"""Django settings for local development."""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".grok.io"]

# Local PostgreSQL database (defaults for empty .env / Docker)
def _dev_db_port():
    val = env.get_value("DB_PORT", default="5432")
    return int(val or "5432")


def _dev_db_str(key: str, default: str):
    val = env.get_value(key, default=default)
    return val or default


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _dev_db_str("DB_NAME", "tcf"),
        "USER": _dev_db_str("DB_USER", "postgres"),
        "PASSWORD": _dev_db_str("DB_PASSWORD", "postgres"),
        "HOST": env.get_value("DB_HOST", default="localhost") or "localhost",
        "PORT": _dev_db_port(),
    }
}

# Local static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Django Debug Toolbar
INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
MIDDLEWARE = (
    MIDDLEWARE[:2]
    + ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    + MIDDLEWARE[2:]
)
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda r: True,
    # Hide the Settings panel to avoid exposing full config dump
    "DISABLE_PANELS": {"debug_toolbar.panels.settings.SettingsPanel"},
}

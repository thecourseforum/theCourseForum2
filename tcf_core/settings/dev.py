"""Django settings for local development and CI."""

import importlib.util

from .base import *

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


DEBUG = ENVIRONMENT == "local"

# Redis-backed cache/sessions like prod when REDIS_URL is set; without a
# shared cache Cachalot invalidations can't reach other processes, so it stays
# off and sessions fall back to plain db.
redis_url = env.str("REDIS_URL", default="")

if redis_url:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": redis_url,
            "KEY_PREFIX": "tcf:dev",
            "OPTIONS": {
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "retry_on_timeout": True,
            },
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
    SESSION_CACHE_ALIAS = "default"
    CACHALOT_ENABLED = True
else:
    CACHALOT_ENABLED = False

# Media via MinIO (S3 backend) when MINIO_ENDPOINT is set; static stays local.
minio_endpoint = env.str("MINIO_ENDPOINT", default="")
if minio_endpoint:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": env.str("MINIO_BUCKET", default="tcf-media"),
                "endpoint_url": minio_endpoint,
                "access_key": env.str("MINIO_ACCESS_KEY", default="minioadmin"),
                "secret_key": env.str("MINIO_SECRET_KEY", default="minioadmin"),
                "addressing_style": "path",
                "file_overwrite": False,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

    # Prod-style manifest statics, opt-in: needs collectstatic re-runs after
    # static changes, and DEBUG=False (Django skips hashing in debug).
    if env.bool("STATIC_S3", default=False):
        DEBUG = False
        STORAGES["staticfiles"] = {
            "BACKEND": "storages.backends.s3.S3ManifestStaticStorage",
            "OPTIONS": {
                "bucket_name": env.str("STATIC_BUCKET", default="tcf-static"),
                "endpoint_url": minio_endpoint,
                "access_key": env.str("MINIO_ACCESS_KEY", default="minioadmin"),
                "secret_key": env.str("MINIO_SECRET_KEY", default="minioadmin"),
                "addressing_style": "path",
                "custom_domain": env.str(
                    "STATIC_CUSTOM_DOMAIN", default="localhost:8081"
                ),
                # storages joins as f"{url_protocol}//{domain}" — colon included.
                "url_protocol": "http:",
            },
        }

# Toolbar only in local mode when the package is installed.
if ENVIRONMENT == "local" and importlib.util.find_spec("debug_toolbar") is not None:
    INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
    MIDDLEWARE = (
        MIDDLEWARE[:2]
        + ["debug_toolbar.middleware.DebugToolbarMiddleware"]
        + MIDDLEWARE[2:]
    )
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda r: True}

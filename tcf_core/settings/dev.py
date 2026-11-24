"""Django settings for local development and CI."""

import importlib.util

from .base import *

ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".grok.io", ".lhr.life"]


DEBUG = ENVIRONMENT == "local"

redis_url = env.str("REDIS_URL", default="redis://tcf_valkey:6379/0")
CACHES = {"default": redis_cache(redis_url, "tcf:dev")}

minio_endpoint = env.str("MINIO_ENDPOINT", default="http://tcf-minio:9000")
STORAGES = {
    "default": s3_storage(
        bucket_name=env.str("MINIO_BUCKET", default="tcf-media"),
        endpoint_url=minio_endpoint,
        access_key=env.str("MINIO_ACCESS_KEY", default="minioadmin"),
        secret_key=env.str("MINIO_SECRET_KEY", default="minioadmin"),
        addressing_style="path",
        file_overwrite=False,
    ),
}

if env.bool("STATIC_MANIFEST", default=False):
    STORAGES["staticfiles"] = MANIFEST_STATIC_STORAGE
    STATIC_URL = f"http://{env.str('STATIC_CUSTOM_DOMAIN', default='localhost:8081')}/"
else:
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }
    STATIC_URL = "/static/"

# Toolbar only in local mode when the package is installed.
if ENVIRONMENT == "local" and importlib.util.find_spec("debug_toolbar") is not None:
    INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
    MIDDLEWARE = (
        MIDDLEWARE[:4]
        + ["debug_toolbar.middleware.DebugToolbarMiddleware"]
        + MIDDLEWARE[4:]
    )
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda r: True,
        # The toolbar's static-files instrumentation instantiates a subclass
        # without the S3 storage options, which breaks django-storages.
        "DISABLE_PANELS": [
            # Both panels wrap storage/profiling state in ways that do not
            # work with the local S3-backed static storage or nested requests.
            "debug_toolbar.panels.staticfiles.StaticFilesPanel",
            "debug_toolbar.panels.profiling.ProfilingPanel",
        ],
    }

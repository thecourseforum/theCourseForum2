"""Django settings for local development and CI."""

import importlib.util

from .base import *

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".grok.io", ".lhr.life"]


DEBUG = ENVIRONMENT == "local"

redis_url = env.str("REDIS_URL", default="redis://tcf_valkey:6379/0")
CACHES = {"default": redis_cache(redis_url, "tcf:dev")}

# Local development and CI use MinIO for media and manifest static files,
# matching production's S3-backed storage and CDN path.
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
    "staticfiles": s3_storage(
        backend="storages.backends.s3.S3ManifestStaticStorage",
        bucket_name=env.str("STATIC_BUCKET", default="tcf-static"),
        endpoint_url=minio_endpoint,
        access_key=env.str("MINIO_ACCESS_KEY", default="minioadmin"),
        secret_key=env.str("MINIO_SECRET_KEY", default="minioadmin"),
        addressing_style="path",
        custom_domain=env.str("STATIC_CUSTOM_DOMAIN", default="localhost:8081"),
        # storages joins as f"{url_protocol}//{domain}" — colon included.
        url_protocol="http:",
    ),
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

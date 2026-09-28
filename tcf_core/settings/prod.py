"""Django settings for AWS production."""

from django.core.exceptions import ImproperlyConfigured

from .base import *

# ECS sets TCF_ENV=prod (iac/ecs.tf); refuse to boot in any other mode.
if ENVIRONMENT != "prod":
    raise ImproperlyConfigured(
        f"tcf_core.settings.prod requires TCF_ENV=prod; got {ENVIRONMENT!r}"
    )

DEBUG = False

DATABASES["default"].update(
    {
        "OPTIONS": {"sslmode": "require"},
        "CONN_MAX_AGE": 60,  # Remove if using RDS proxy
    }
)

ALLOWED_HOSTS = [
    "*",
    "thecourseforum.com",
    "thecourseforumtest.com",
    env.str("AWS_ELB_URL"),
    env.str("AWS_CLOUDFRONT_URL"),
]

# AWS S3 for static files
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_CUSTOM_DOMAIN = env.str(
    "AWS_S3_CUSTOM_DOMAIN", default=f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
)
AWS_DEFAULT_ACL = None

STORAGES = {
    "default": s3_storage(
        object_parameters={"CacheControl": "max-age=86400"},
    ),
    "staticfiles": s3_storage(
        backend="storages.backends.s3.S3ManifestStaticStorage",
        object_parameters={"CacheControl": "public, max-age=31536000, immutable"},
    ),
}

CACHES = {"default": redis_cache(env.str("AWS_REDIS_URL"), "tcf:prod")}

CACHALOT_TIMEOUT = 60 * 60 * 24 * 7  # 1 week

# Security
CSRF_TRUSTED_ORIGINS = [
    "https://thecourseforum.com",
    "https://thecourseforumtest.com",
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

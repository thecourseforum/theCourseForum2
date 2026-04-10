"""Django settings for AWS production."""

from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "*",
    "thecourseforum.com",
    "thecourseforumtest.com",
    env.str("AWS_ELB_URL"),
    env.str("AWS_CLOUDFRONT_URL"),
]

# AWS S3 for static files
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_CUSTOM_DOMAIN = env.str(
    "AWS_S3_CUSTOM_DOMAIN", default=f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
)
AWS_DEFAULT_ACL = None

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {"object_parameters": {"CacheControl": "max-age=86400"}},
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3.S3ManifestStaticStorage",
        "OPTIONS": {
            "object_parameters": {"CacheControl": "public, max-age=31536000, immutable"}
        },
    },
}

# AWS RDS PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("AWS_RDS_NAME"),
        "USER": env.str("AWS_RDS_USER"),
        "PASSWORD": env.str("AWS_RDS_PASSWORD"),
        "HOST": env.str("AWS_RDS_HOST"),
        "PORT": env.int("AWS_RDS_PORT"),
        "OPTIONS": {"sslmode": "require"},
        "CONN_MAX_AGE": 60,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("AWS_REDIS_URL"),
    }
}

# Security
CSRF_TRUSTED_ORIGINS = [
    "https://thecourseforum.com",
    "https://thecourseforumtest.com",
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

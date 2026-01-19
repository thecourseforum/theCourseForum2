# pylint: disable=unused-wildcard-import,wildcard-import
"""Django settings for AWS production."""
from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "*",
    "thecourseforum.com",
    "thecourseforumtest.com",
    "tcf-load-balancer-1374896025.us-east-1.elb.amazonaws.com",
    "d1gr9vmyo0mkxv.cloudfront.net",
]

# AWS S3 for static files
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_CUSTOM_DOMAIN = env.str(
    "AWS_S3_CUSTOM_DOMAIN", default=f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
)
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": {}},
    "staticfiles": {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": { "location": "static" } },
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
    }
}

# Security
CSRF_TRUSTED_ORIGINS = [
    "https://thecourseforum.com",
    "https://thecourseforumtest.com",
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

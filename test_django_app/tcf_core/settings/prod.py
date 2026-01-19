"""
Django production settings for AWS deployment.
"""
from .base import *

DEBUG = False

# Allowed hosts - set via environment variable
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Security settings for production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# AWS RDS PostgreSQL Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.str('AWS_RDS_NAME'),
        'USER': env.str('AWS_RDS_USER'),
        'PASSWORD': env.str('AWS_RDS_PASSWORD'),
        'HOST': env.str('AWS_RDS_HOST'),
        'PORT': env.int('AWS_RDS_PORT', default=5432),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# AWS S3 Settings for static and media files
AWS_STORAGE_BUCKET_NAME = env.str('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = env.str('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = env.str(
    'AWS_S3_CUSTOM_DOMAIN',
    default=f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
)
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Storage configuration for S3
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "location": "media",
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "location": "static",
        },
    },
}

# Static files URL
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Media files URL
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': env.str('DJANGO_LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env.str('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

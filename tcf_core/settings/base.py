# pylint: disable=fixme
"""Base Django settings for tcf_core project."""
import os

import environ
from django.contrib.messages import constants as messages
from django.urls import reverse_lazy

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django-environ library imports .env settings
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
)
env_file = os.path.join(BASE_DIR, ".env")
environ.Env.read_env(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG")  # default value set on the top

ALLOWED_HOSTS = []

CORS_ALLOWED_ORIGINS = [
    "https://thecourseforum.com",
    "https://thecourseforumtest.com",
    "https://pagead2.googlesyndication.com",
    "https://securepubads.g.doubleclick.net",
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # "collectfast",
    "django.contrib.staticfiles",
    "cachalot",  # TODO: add Redis?
    "storages",
    "rest_framework",
    "django_filters",
    "tcf_website",
]

# Dev does not use S3 buckets
if env.str("ENVIRONMENT") == "dev":
    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    ALLOWED_HOSTS.extend(["localhost", ".grok.io", "127.0.0.1"])

    DATABASES = {
        "default": {
            "NAME": env.str("DB_NAME"),
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "USER": env.str("DB_USER"),
            "PASSWORD": env.str("DB_PASSWORD"),
            "HOST": env.str("DB_HOST"),
            "PORT": env.int("DB_PORT"),
        }
    }
else:
    AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

    ALLOWED_HOSTS.extend(
        [
            "tcf-load-balancer-1374896025.us-east-1.elb.amazonaws.com",
            "thecourseforum.com",
            "thecourseforumtest.com",
        ]
    )

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {},
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
    }

    DATABASES = {
        "default": {
            "NAME": env.str("AWS_RDS_NAME"),
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "USER": env.str("AWS_RDS_USER"),
            "PASSWORD": env.str("AWS_RDS_PASSWORD"),
            "HOST": env.str("AWS_RDS_HOST"),
            "PORT": env.int("AWS_RDS_PORT"),
        }
    }

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "tcf_core.cognito_middleware.CognitoAuthMiddleware",
    "tcf_core.settings.handle_exceptions_middleware.HandleExceptionsMiddleware",
    "tcf_core.settings.record_middleware.RecordMiddleware",
]

ROOT_URLCONF = "tcf_core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tcf_core.context_processors.base",
                "tcf_core.context_processors.searchbar_context",
            ],
        },
    },
]

WSGI_APPLICATION = "tcf_core.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# social-auth-app-django settings.

# AWS Cognito Configuration
COGNITO_USER_POOL_ID = env.str("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = env.str("COGNITO_APP_CLIENT_ID")
COGNITO_APP_CLIENT_SECRET = env.str("COGNITO_APP_CLIENT_SECRET")
COGNITO_DOMAIN = env.str("COGNITO_DOMAIN")
COGNITO_REGION_NAME = env.str("COGNITO_REGION_NAME")

# These should match exactly what you configured in Cognito
COGNITO_REDIRECT_URI = "/cognito-callback"
COGNITO_LOGOUT_URI = "/"

# Replace social auth backends with custom Cognito backend
AUTHENTICATION_BACKENDS = (
    "tcf_website.auth_backends.CognitoBackend",
    "django.contrib.auth.backends.ModelBackend",
)

# Login URL for redirecting unauthenticated users
LOGIN_URL = reverse_lazy("login")

AUTH_USER_MODEL = "tcf_website.User"

# Logging configuration (from https://docs.djangoproject.com/en/3.1/topics/logging/)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Django Rest Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

# Automated email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")

# Import review drive settings
REVIEW_DRIVE_ID = env.str("REVIEW_DRIVE_ID", default=None)
REVIEW_DRIVE_EMAIL = env.str("REVIEW_DRIVE_EMAIL", default=None)
REVIEW_DRIVE_PASSWORD = env.str("REVIEW_DRIVE_PASSWORD", default=None)

# Use Bootstrap class names for Django message tags
MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

# Required in Django 3.2+ (See https://stackoverflow.com/a/66971803)
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Toxicity threshold for filtering reviews
TOXICITY_THRESHOLD = 74

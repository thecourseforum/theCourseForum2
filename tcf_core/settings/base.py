"""Base Django settings for tcf_core project."""

import os

import environ
from django.contrib.messages import constants as messages
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django-environ library imports .env settings
env = environ.Env()
env_file = os.path.join(BASE_DIR, ".env")
environ.Env.read_env(env_file)

# Runtime mode, set by the launcher: local (default) | ci | prod.
ENVIRONMENT = env.str("TCF_ENV", default="local")
if ENVIRONMENT not in ("local", "ci", "prod"):
    raise ImproperlyConfigured(
        f"TCF_ENV must be one of 'local', 'ci', 'prod'; got {ENVIRONMENT!r}"
    )


def _database_env(name):
    prefixes = ("AWS_RDS_", "DB_") if ENVIRONMENT == "prod" else ("DB_", "AWS_RDS_")
    for prefix in prefixes:
        value = os.environ.get(f"{prefix}{name}")
        if value:
            return value
    raise ImproperlyConfigured(
        f"Missing database setting: {prefixes[0]}{name} or {prefixes[1]}{name}"
    )


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _database_env("NAME"),
        "USER": _database_env("USER"),
        "PASSWORD": _database_env("PASSWORD"),
        "HOST": _database_env("HOST"),
        "PORT": int(_database_env("PORT")),
    }
}


def redis_cache(location, key_prefix):
    return {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": location,
        "KEY_PREFIX": key_prefix,
        "OPTIONS": {
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True,
        },
    }


def s3_storage(
    *,
    backend="storages.backends.s3.S3Storage",
    bucket_name=None,
    endpoint_url=None,
    access_key=None,
    secret_key=None,
    addressing_style=None,
    file_overwrite=None,
    custom_domain=None,
    url_protocol=None,
    object_parameters=None,
):
    options = {
        "bucket_name": bucket_name,
        "endpoint_url": endpoint_url,
        "access_key": access_key,
        "secret_key": secret_key,
        "addressing_style": addressing_style,
        "file_overwrite": file_overwrite,
        "custom_domain": custom_domain,
        "url_protocol": url_protocol,
        "object_parameters": object_parameters,
    }
    return {
        "BACKEND": backend,
        "OPTIONS": {key: value for key, value in options.items() if value is not None},
    }


SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"
CACHALOT_ENABLED = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

OPENROUTER_API_KEY = env.str("OPENROUTER_API_KEY", default="")

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
    "cachalot",
    "storages",
    "rest_framework",
    "django_filters",
    "tcf_website",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "tcf_core.settings.health_check_middleware.HealthCheckMiddleware",
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


# AWS Cognito Configuration (optional - only needed for auth features)
COGNITO_USER_POOL_ID = env.str("COGNITO_USER_POOL_ID", default="")
COGNITO_APP_CLIENT_ID = env.str("COGNITO_APP_CLIENT_ID", default="")
COGNITO_APP_CLIENT_SECRET = env.str("COGNITO_APP_CLIENT_SECRET", default="")
COGNITO_DOMAIN = env.str("COGNITO_DOMAIN", default="")
COGNITO_REGION_NAME = env.str("COGNITO_REGION_NAME", default="us-east-1")
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

# Review drive settings (optional, for load_review_drive command)
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

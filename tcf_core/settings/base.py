# pylint: disable=fixme
"""Base Django settings for tcf_core project."""

import os

import environ
import sentry_sdk
from django.contrib.messages import constants as messages
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration

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
    "cachalot",  # TODO: add Redis?
    "storages",
    "rest_framework",
    "django_filters",
    "tcf_website",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
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

# Sentry error tracking and performance monitoring
SENTRY_DSN = env.str("SENTRY_DSN", default=None)
SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE", default=1.0)
SENTRY_PROFILES_SAMPLE_RATE = env.float("SENTRY_PROFILES_SAMPLE_RATE", default=1.0)

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        # Add data like request headers and IP for users
        send_default_pii=True,
        # Only send ERROR and above to Sentry (CloudWatch handles INFO/DEBUG)
        enable_logs=True,
        event_level="error",  # Only ERROR, CRITICAL go to Sentry as events
        # Sample performance traces (1.0 = 100%, adjustable via env var)
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        # Sample profiling (1.0 = 100%, adjustable via env var)
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
        # Ignore common noise
        ignore_errors=[
            KeyboardInterrupt,
            # Add other exceptions to ignore if needed
        ],
        before_send=_sentry_before_send,
    )


def _sentry_before_send(event, hint):
    """Filter out noise before sending to Sentry."""
    # Ignore 404 errors
    if event.get("logger") == "django.request":
        if "exception" in event:
            exc_type = event["exception"]["values"][0].get("type")
            if exc_type == "Http404":
                return None

    # Add request_id from context
    from tcf_core.request_logging import request_context
    context = request_context.get()
    if context:
        event.setdefault("tags", {})
        event["tags"]["request_id"] = context.get("request_id")

    return event

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

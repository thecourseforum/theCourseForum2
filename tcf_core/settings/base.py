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

ALLOWED_HOSTS = ["localhost", ".ngrok.io", "127.0.0.1"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "social_django",
    "cachalot",  # TODO: add Redis?
    "rest_framework",
    "django_filters",
    "tcf_website",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "tcf_core.context_processors.base",
                "tcf_core.context_processors.history_cookies",
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


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/")


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "NAME": env.str("DB_NAME"),
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "USER": env.str("DB_USER"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": env.str("DB_HOST"),
        "PORT": env.int("DB_PORT"),
    },
    "legacy": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "tcf.db"),
    },
}


# social-auth-app-django settings.

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.email.EmailAuth",
    "django.contrib.auth.backends.ModelBackend",
)
# TODO: Look into options like SOCIAL_AUTH_LOGIN_ERROR_URL or LOGIN_ERROR_URL
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")
# SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS = ["virginia.edu"]
SOCIAL_AUTH_LOGIN_REDIRECT_URL = reverse_lazy("browse")

SOCIAL_AUTH_EMAIL_FORM_URL = "/"
EMAIL_VALIDATION_URL = "email_verification"
SOCIAL_AUTH_EMAIL_VALIDATION_FUNCTION = "tcf_core.auth_pipeline.validate_email"
# SOCIAL_AUTH_EMAIL_AUTH_WHITELISTED_DOMAINS = ["virginia.edu"]

# WHITELISTED_DOMAINS = ["virginia.edu"]


SOCIAL_AUTH_GOOGLE_OAUTH2_LOGIN_URL = reverse_lazy("social:begin", args=["google-oauth2"])
SOCIAL_AUTH_RAISE_EXCEPTIONS = False
SOCIAL_AUTH_PIPELINE = (
    "tcf_core.auth_pipeline.password_validation",
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "tcf_core.auth_pipeline.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "tcf_core.auth_pipeline.mail_validation",
    "social_core.pipeline.social_auth.associate_by_email",
    "tcf_core.auth_pipeline.collect_extra_info",
    "tcf_core.auth_pipeline.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "tcf_core.auth_pipeline.check_user_password",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)
SOCIAL_AUTH_USER_MODEL = "tcf_website.User"

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

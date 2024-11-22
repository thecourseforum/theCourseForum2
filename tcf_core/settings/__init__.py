# pylint: disable=unused-wildcard-import,wildcard-import
"""
Django settings module for local development environment. This is the default
Django settings file that will be used in case the environment variable
`DJANGO_SETTINGS_MODULE` is not set.
"""
from .base import *
from .celery_init import celery_app

__all__ = ('celery_app',) 

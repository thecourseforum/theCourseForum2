# pylint: disable=unused-wildcard-import,wildcard-import
"""Django settings module for local development environment"""
from .base import *


# django-silk settings
def custom_recording_logic(request):
    """
    Exclude API views for django-silk

    This can be replaced by a lambda function, but autopep8 won't allow that :(
    """
    return not request.path.startswith('/api')


# Performance profiling for non-API views during development
INSTALLED_APPS.append('silk')
MIDDLEWARE.append('silk.middleware.SilkyMiddleware')
SILKY_INTERCEPT_FUNC = custom_recording_logic

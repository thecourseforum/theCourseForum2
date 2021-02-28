# pylint: disable=unused-wildcard-import,wildcard-import
"""
Django settings module for local development environment. This is the default
Django settings file that will be used in case the environment variable
`DJANGO_SETTINGS_MODULE` is not set.
"""
from .base import *


# django-silk settings
def custom_recording_logic(request):
    """
    Exclude API views for django-silk

    This can be replaced by a lambda function, but autopep8 won't allow that :(
    """
    return not request.path.startswith('/api')


if os.environ.get('DJANGO_SETTINGS_MODULE') not in [
        'tcf_core.settings.dev', 'tcf_core.settings.prod']:
    # Performance profiling for non-API views during development
    INSTALLED_APPS.append('silk')
    MIDDLEWARE.append('silk.middleware.SilkyMiddleware')
    SILKY_INTERCEPT_FUNC = custom_recording_logic

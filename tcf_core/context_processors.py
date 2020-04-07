"""Inject extra context to TCF templates."""
from django.conf import settings

from tcf_website.models import Semester


def base(request):
    """Inject user + latest semester info."""
    return {
        'DEBUG': settings.DEBUG,
        'USER': request.user,
        'LATEST_SEMESTER': Semester.latest()}

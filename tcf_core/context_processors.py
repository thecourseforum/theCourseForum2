"""Inject extra context to TCF templates."""

from django.conf import settings

from django.core.cache import cache
from tcf_website.models import Discipline, Semester, Subdepartment


def base(request):
    """Inject user + latest semester info."""
    return {
        "DEBUG": settings.DEBUG,
        "USER": request.user,
        "LATEST_SEMESTER": Semester.latest(),
    }


def searchbar_context(request):
    """Provide context for the search bar."""
    cache_key = "tcf_searchbar_context_v1"
    ctx = cache.get(cache_key)
    if ctx is not None:
        return ctx

    latest_semester = Semester.latest()
    recent_semesters = list(
        Semester.objects.filter(
            number__gte=latest_semester.number - 50  # 50 = 5 years * 10 semesters
        ).order_by("-number")
    )

    disciplines = list(Discipline.objects.all().order_by("name"))
    subdepartments = list(Subdepartment.objects.all().order_by("mnemonic"))

    ctx = {
        "disciplines": disciplines,
        "subdepartments": subdepartments,
        "semesters": recent_semesters,
    }
    # Cache for 24 hours; data changes rarely
    cache.set(cache_key, ctx, 60 * 60 * 24)
    return ctx

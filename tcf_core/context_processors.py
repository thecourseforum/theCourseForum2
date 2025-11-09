"""Inject extra context to TCF templates."""

from django.conf import settings

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
    latest_semester = Semester.latest()
    recent_semesters = Semester.objects.filter(
        number__gte=latest_semester.number - 50  # 50 = 5 years * 10 semesters
    ).order_by("-number")

    # Provide only the data needed for the filter options
    # Filter values are managed by localStorage on the client side
    context = {
        "disciplines": Discipline.objects.all().order_by("name"),
        "subdepartments": Subdepartment.objects.all().order_by("mnemonic"),
        "semesters": recent_semesters,
    }
    return context


def flags(_request):
    """Expose template context flags.

    _request is unused.

    Returns a dict containing ENABLE_CLUB_CALENDAR with its default.
    """
    return {
        "ENABLE_CLUB_CALENDAR": getattr(settings, "ENABLE_CLUB_CALENDAR", False),
    }

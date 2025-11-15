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
    """
    Builds template context used by the site search bar.
    
    Provides a mapping with the following keys:
    - "disciplines": QuerySet of all Discipline objects ordered by name.
    - "subdepartments": QuerySet of all Subdepartment objects ordered by mnemonic.
    - "semesters": QuerySet of recent Semester objects; if no latest Semester exists, an empty QuerySet is returned, otherwise semesters with number greater than or equal to latest.number - 50 ordered by descending number.
    """
    latest_semester = Semester.latest()
    if latest_semester is None:
        recent_semesters = Semester.objects.none()
    else:
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
    """
    Provide feature flags for templates.
    
    The `_request` argument is unused.
    
    Returns:
        dict: Mapping containing `"ENABLE_CLUB_CALENDAR"` set to the value of
        `settings.ENABLE_CLUB_CALENDAR` if defined, otherwise `False`.
    """
    return {
        "ENABLE_CLUB_CALENDAR": getattr(settings, "ENABLE_CLUB_CALENDAR", False),
    }
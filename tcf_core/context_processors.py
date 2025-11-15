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
    Provide template context for a search bar with discipline, subdepartment, and recent semester options.
    
    Returns:
        context (dict): Mapping with:
            - 'disciplines': QuerySet of all Discipline objects ordered by name.
            - 'subdepartments': QuerySet of all Subdepartment objects ordered by mnemonic.
            - 'semesters': QuerySet of recent Semester objects (semesters whose number is within 50 of the latest semester, ordered by descending number), or an empty QuerySet if no latest semester exists.
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
    Expose template context flags for templates.
    
    Parameters:
        _request: The incoming request (unused).
    
    Returns:
        A dict with the key "ENABLE_CLUB_CALENDAR" set to the value of
        settings.ENABLE_CLUB_CALENDAR if present, otherwise False.
    """
    return {
        "ENABLE_CLUB_CALENDAR": getattr(settings, "ENABLE_CLUB_CALENDAR", False),
    }
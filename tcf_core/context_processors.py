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

    # No longer use session to store filters
    # Empty defaults are provided instead
    context = {
        "disciplines": Discipline.objects.all().order_by("name"),
        "subdepartments": Subdepartment.objects.all().order_by("mnemonic"),
        "semesters": recent_semesters,
        "selected_disciplines": [],
        "selected_subdepartments": [],
        "selected_weekdays": [],
        "from_time": "",
        "to_time": "",
        "open_sections": False,
        "min_gpa": 0.0,
    }
    return context

"""Department listing view."""

from urllib.parse import unquote_plus

from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from ...models import Department, Semester


def department(request, dept_id: int, course_recency=None):
    """View for department page."""
    dept = get_object_or_404(
        Department.objects.prefetch_related("subdepartment_set"), pk=dept_id
    )

    if not course_recency:
        course_recency = str(Semester.latest())
    else:
        # Decode URL-encoded spaces (e.g., Fall+2021 -> Fall 2021)
        course_recency = unquote_plus(course_recency)

    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, None, True),
    ]

    latest_semester = Semester.latest()
    last_five_years = get_object_or_404(Semester, number=latest_semester.number - 50)
    season, year = course_recency.upper().split()
    active_semester = Semester.objects.filter(year=year, season=season).first()

    num_of_years = latest_semester.year - int(year)
    courses = list(dept.fetch_recent_courses(num_of_years))

    return render(
        request,
        "site/catalog/department.html",
        {
            "dept_id": dept_id,
            "latest_semester": str(latest_semester),
            "breadcrumbs": breadcrumbs,
            "courses": courses,
            "active_course_recency": str(active_semester),
            "last_five_years": str(last_five_years),
        },
    )

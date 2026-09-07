"""Department listing view."""

from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from ...models import Department
from ...pagination import paginate

_PAGE_SIZE = 20


def department(request, dept_id: int):
    """View for department page."""
    dept = get_object_or_404(
        Department.objects.prefetch_related("subdepartment_set"), pk=dept_id
    )

    latest_only = request.GET.get("latest", "true") != "false"
    page_obj = paginate(
        dept.fetch_recent_courses(latest_only=latest_only),
        request.GET.get("page", 1),
        per_page=_PAGE_SIZE,
    )

    return render(
        request,
        "site/catalog/department.html",
        {
            "dept_id": dept_id,
            "breadcrumbs": [
                (dept.school.name, reverse("browse"), False),
                (dept.name, None, True),
            ],
            "page_obj": page_obj,
            "latest_only": latest_only,
        },
    )

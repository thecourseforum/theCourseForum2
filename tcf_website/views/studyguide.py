"""Views for per-course Study Guide pages.

Separates Study Guide logic from browse/views to keep responsibilities focused.
"""

from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..models import Course, Semester


@login_required
def study_guide(request, mnemonic: str, course_number: int):
    """Render Study Guide page for a specific course.

    - Resolves the course by mnemonic and number
    - Constructs a deterministic room_id for realtime collaboration
    - Provides breadcrumbs consistent with other course pages
    """

    course = get_object_or_404(
        Course,
        subdepartment__mnemonic=mnemonic.upper(),
        number=course_number,
    )

    latest_semester = Semester.latest()

    # Include current semester (e.g., spring-2025) in room_id for per-semester guides
    semester_slug = f"{latest_semester.season.lower()}-{latest_semester.year}"
    room_id = f"studyguide-{course.subdepartment.mnemonic}-{course.number}-{semester_slug}"

    dept = course.subdepartment.department
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, reverse("course", args=[course.subdepartment.mnemonic, course.number]), False),
        ("Study Guide", None, True),
    ]

    context = {
        "course": course,
        "room_id": room_id,
        "is_authenticated": request.user.is_authenticated,
        "user_display": getattr(request.user, "username", "anonymous") or "anonymous",
        "latest_semester": str(latest_semester),
        "breadcrumbs": breadcrumbs,
        "liveblocks_public_key": getattr(settings, "LIVEBLOCKS_PUBLIC_KEY", None),
    }

    return render(request, "course/study_guide.html", context)
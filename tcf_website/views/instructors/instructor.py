"""Instructor profile view."""

# pylint: disable=too-many-locals

from typing import Any

from django.db.models import Avg
from django.shortcuts import get_object_or_404, render

from ...models import Instructor, Semester
from ...utils import safe_round


def instructor_view(request, instructor_id):
    """Instructor view."""
    instructor: Instructor = get_object_or_404(Instructor, pk=instructor_id)

    stats: dict[str, float] = Instructor.objects.filter(pk=instructor.pk).aggregate(
        avg_gpa=Avg("courseinstructorgrade__average"),
        avg_difficulty=Avg("review__difficulty"),
        avg_rating=(
            Avg("review__instructor_rating")
            + Avg("review__enjoyability")
            + Avg("review__recommendability")
        )
        / 3,
    )

    courses = list(instructor.get_course_summaries())
    is_teaching_current_semester = any(course.get("is_current") for course in courses)

    semester_numbers = {
        num for num in (c.get("latest_semester_number") for c in courses) if num
    }
    semester_info = {
        s["number"]: (s["season"], s["year"])
        for s in Semester.objects.filter(number__in=semester_numbers).values(
            "number", "season", "year"
        )
    }

    grouped_courses: dict[str, list[dict[str, Any]]] = {}
    for course in courses:
        sem_num = course.pop("latest_semester_number", None)
        if sem_num and sem_num in semester_info:
            season, year = semester_info[sem_num]
            course["last_taught"] = f"{season} {year}".title()
        else:
            course["last_taught"] = "—"

        grouped_courses.setdefault(course["subdepartment_name"], []).append(course)

    context: dict[str, Any] = {
        "instructor": instructor,
        **{key: safe_round(value) for key, value in stats.items()},
        "courses": grouped_courses,
        "is_teaching_current_semester": is_teaching_current_semester,
    }
    return render(request, "site/instructors/instructor.html", context)

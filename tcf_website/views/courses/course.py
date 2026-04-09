"""Course page view and section-time helpers used on that page."""

# pylint: disable=too-many-locals

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ...models import Course, Section, Semester


def is_lecture_section(section_type: str | None) -> bool:
    """Return True when a section type should be treated as lecture."""
    if not section_type:
        return True
    normalized = section_type.strip().lower()
    return normalized.startswith("lec")


def split_section_times(section_times: str) -> list[str]:
    """Convert comma-separated section times into a clean list."""
    if not section_times:
        return []
    return [
        entry.strip() for entry in section_times.rstrip(",").split(",") if entry.strip()
    ]


def build_section_times_maps_by_instructor(
    course_id: int, semester: Semester
) -> tuple[dict[int, dict[str, list[str]]], dict[int, dict[str, list[str]]]]:
    """Build all-sections and lecture-only section-time maps keyed by instructor ID."""
    all_times_by_instructor: dict[int, dict[str, list[str]]] = {}
    lecture_times_by_instructor: dict[int, dict[str, list[str]]] = {}

    sections = (
        Section.objects.filter(course_id=course_id, semester=semester)
        .prefetch_related("instructors")
        .order_by("sis_section_number")
    )

    for section in sections:
        times = split_section_times(section.section_times)
        if not times:
            continue

        section_number = str(section.sis_section_number)
        for section_instructor in section.instructors.all():
            all_times_by_instructor.setdefault(section_instructor.id, {})[
                section_number
            ] = times
            if is_lecture_section(section.section_type):
                lecture_times_by_instructor.setdefault(section_instructor.id, {})[
                    section_number
                ] = times

    return all_times_by_instructor, lecture_times_by_instructor


def course_view(request, mnemonic: str, course_number: int):
    """Course view."""
    if mnemonic != mnemonic.upper():
        return redirect(
            "course", mnemonic=mnemonic.upper(), course_number=course_number
        )

    course = get_object_or_404(
        Course,
        subdepartment__mnemonic=mnemonic.upper(),
        number=course_number,
    )

    latest_semester = Semester.latest()
    latest_only = request.GET.get("latest", "true") != "false"
    sortby = request.GET.get("sortby", "last_taught")
    order = request.GET.get("order", "desc")

    instructors = list(
        course.sort_instructors_by_key(latest_semester, latest_only, order, sortby)
    )

    all_times_by_instructor, lecture_times_by_instructor = (
        build_section_times_maps_by_instructor(course.id, latest_semester)
    )

    sem_ids = {i.semester_last_taught for i in instructors if i.semester_last_taught}
    sems = {s.pk: s for s in Semester.objects.filter(pk__in=sem_ids)}
    for instructor in instructors:
        sem = sems.get(instructor.semester_last_taught)
        instructor.semester_last_taught = str(sem) if sem else "Unknown"
        instructor.times = lecture_times_by_instructor.get(instructor.id, {})
        instructor.all_times = all_times_by_instructor.get(instructor.id, {})

    dept = course.subdepartment.department

    return render(
        request,
        "site/courses/course.html",
        {
            "course": course,
            "instructors": instructors,
            "breadcrumbs": [
                (dept.school.name, reverse("browse"), False),
                (dept.name, reverse("department", args=[dept.pk]), False),
                (course.code, None, True),
            ],
            "sortby": sortby,
            "order": order,
            "course_code": course.code(),
            "course_title": course.title,
            "all_section_times_by_instructor": all_times_by_instructor,
        },
    )

"""Course–instructor (pair) page view."""

import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count, Q
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse

from ...models import CourseInstructorGrade, Review, ReviewLLMSummary, Section, Semester
from .course import is_lecture_section

_GRADE_BREAKDOWN_FIELDS = (
    "a_plus",
    "a",
    "a_minus",
    "b_plus",
    "b",
    "b_minus",
    "c_plus",
    "c",
    "c_minus",
    "dfw",
    "total_enrolled",
)


def _fetch_pair_section_anchor(course_id, instructor_id):
    """Latest Section row for this course–instructor pair, or 404."""
    section_last_taught = (
        Section.objects.filter(course_id=course_id, instructors__id=instructor_id)
        .order_by("-semester__number")
        .select_related("course", "semester")
        .prefetch_related("instructors")
        .first()
    )
    if section_last_taught is None:
        raise Http404
    course = section_last_taught.course
    instructor = section_last_taught.instructors.get(pk=instructor_id)
    return section_last_taught, course, instructor


def _pair_review_counts(course_id, instructor_id):
    """Counts for ratings vs written reviews (toxicity filter matches main queryset)."""
    row = Review.objects.filter(
        instructor=instructor_id,
        course=course_id,
        toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
    ).aggregate(
        num_ratings=Count("id"),
        num_reviews=Count("id", filter=~Q(text="")),
    )
    return row["num_reviews"], row["num_ratings"]


def _pair_aggregate_chart_data(course, instructor, course_id, instructor_id):
    """Averages and optional grade breakdown for the instructor page JSON blob."""
    data = Review.objects.filter(course=course_id, instructor=instructor_id).aggregate(
        average_rating=(
            Avg("instructor_rating") + Avg("enjoyability") + Avg("recommendability")
        )
        / 3,
        instructor=Avg("instructor_rating"),
        enjoyability=Avg("enjoyability"),
        difficulty=Avg("difficulty"),
        recommendability=Avg("recommendability"),
        hours=Avg("hours_per_week"),
        amount_reading=Avg("amount_reading"),
        amount_writing=Avg("amount_writing"),
        amount_group=Avg("amount_group"),
        amount_homework=Avg("amount_homework"),
    )
    # Pass raw floats to JS; each display call (toFixed) rounds to the needed precision.
    # Pre-rounding here would cause double-rounding divergence from Django's floatformat.

    try:
        grades_data = CourseInstructorGrade.objects.get(
            instructor=instructor, course=course
        )
    except ObjectDoesNotExist:
        pass
    else:
        data["average_gpa"] = (
            round(grades_data.average, 2) if grades_data.average else None
        )
        for field in _GRADE_BREAKDOWN_FIELDS:
            data[field] = getattr(grades_data, field)

    return data


def _pair_sections_this_semester(course_id, instructor_id, semester):
    """Lecture vs other sections for the given semester."""
    lecture_sections = []
    other_sections = []
    sections_qs = Section.objects.filter(
        course_id=course_id, instructors__id=instructor_id, semester=semester
    ).order_by("sis_section_number")

    for section in sections_qs:
        times_display = ""
        if section.section_times:
            times_display = section.section_times.rstrip(",")

        section_data = {
            "number": section.sis_section_number,
            "type": section.section_type or "Section",
            "units": section.units,
            "times": times_display,
            "enrollment_taken": section.enrollment_taken or 0,
            "enrollment_limit": section.enrollment_limit or 0,
            "waitlist_taken": section.waitlist_taken or 0,
            "waitlist_limit": section.waitlist_limit or 0,
        }
        if is_lecture_section(section.section_type):
            lecture_sections.append(section_data)
        else:
            other_sections.append(section_data)

    return lecture_sections, other_sections


def _get_review_summary(course_id, instructor_id):
    """Return ReviewLLMSummary for this pair, or None."""
    try:
        return ReviewLLMSummary.objects.get(
            course_id=course_id, instructor_id=instructor_id
        )
    except ReviewLLMSummary.DoesNotExist:
        return None


def _course_instructor_breadcrumbs(course, instructor):
    dept = course.subdepartment.department
    course_url = reverse("course", args=[course.subdepartment.mnemonic, course.number])
    return [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, course_url, False),
        (instructor.full_name, None, True),
    ]


def course_instructor(
    request, course_id, instructor_id, method="Default"
):  # pylint: disable=too-many-locals
    """Course-instructor view."""
    section_last_taught, course, instructor = _fetch_pair_section_anchor(
        course_id, instructor_id
    )

    num_reviews, num_ratings = _pair_review_counts(course_id, instructor_id)

    sort_method = request.GET.get("sort", method)
    page_number = request.GET.get("page", 1)
    paginated_reviews = Review.get_paginated_reviews(
        course_id, instructor_id, request.user, page_number, sort_method
    )

    breadcrumbs = _course_instructor_breadcrumbs(course, instructor)
    data = _pair_aggregate_chart_data(course, instructor, course_id, instructor_id)
    review_summary = _get_review_summary(course_id, instructor_id)

    latest_semester = Semester.latest()
    is_current_semester = section_last_taught.semester.number == latest_semester.number

    if is_current_semester:
        lecture_sections, other_sections = _pair_sections_this_semester(
            course_id, instructor_id, latest_semester
        )
    else:
        lecture_sections, other_sections = [], []

    return render(
        request,
        "site/courses/course_instructor.html",
        {
            "course": course,
            "course_id": course_id,
            "instructor": instructor,
            "semester_last_taught": section_last_taught.semester,
            "num_ratings": num_ratings,
            "num_reviews": num_reviews,
            "paginated_reviews": paginated_reviews,
            "breadcrumbs": breadcrumbs,
            "data": json.dumps(data),
            "display_times": latest_semester == section_last_taught.semester,
            "is_current_semester": is_current_semester,
            "sort_method": sort_method,
            "sem_code": section_last_taught.semester.number,
            "course_code": course.code(),
            "course_title": course.title,
            "instructor_fullname": instructor.full_name,
            "lecture_sections": lecture_sections,
            "other_sections": other_sections,
            "sections_count": len(lecture_sections) + len(other_sections),
            "show_schedule_add": is_current_semester
            and bool(lecture_sections or other_sections),
            "review_summary": review_summary,
        },
    )

"""XHR preflight and cascade option endpoints for review submission."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from ...models import Course
from ...review.forms import ReviewForm
from ...review.services import (
    instructors_for_course_semester,
    is_duplicate_review_for_user,
    recent_semester_id_set,
)
from ...utils import semesters_for_course


def _review_preflight_wants_json(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _review_preflight_invalid_form_response(request, form: ReviewForm):
    if _review_preflight_wants_json(request):
        return JsonResponse(
            {
                "ok": False,
                "error": "Invalid review data.",
                "errors": form.errors.get_json_data(),
            },
            status=400,
        )
    return redirect("new_review")


@login_required
def check_duplicate(request):
    """Check for duplicate reviews when a user submits a review."""
    form = ReviewForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        dup = is_duplicate_review_for_user(request.user, instance)
        return JsonResponse({"duplicate": dup})
    return _review_preflight_invalid_form_response(request, form)


@login_required
def check_zero_hours_per_week(request):
    """Check that user hasn't submitted 0 *total* hours/week for a given course/review."""
    form = ReviewForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        if instance.hours_per_week == 0:
            return JsonResponse({"zero": True})
        return JsonResponse({"zero": False})
    return _review_preflight_invalid_form_response(request, form)


@login_required
def review_semester_options(request):
    """Return terms (recent catalog window) in which a course has at least one section."""
    try:
        course_id = int(request.GET["course"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "course required"}, status=400)

    course = get_object_or_404(Course, id=course_id)
    rows = [{"id": s.id, "label": str(s)} for s in semesters_for_course(course)]
    return JsonResponse({"semesters": rows})


@login_required
def review_instructor_options(request):
    """Return instructors teaching a course in a semester (for review cascade XHR)."""
    try:
        course_id = int(request.GET["course"])
        semester_id = int(request.GET["semester"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "course and semester required"}, status=400)

    if semester_id not in recent_semester_id_set():
        return JsonResponse({"error": "invalid semester"}, status=400)

    get_object_or_404(Course, id=course_id)

    rows = [
        {"id": i.id, "last_name": i.last_name, "first_name": i.first_name}
        for i in instructors_for_course_semester(course_id, semester_id)
    ]
    return JsonResponse({"instructors": rows})

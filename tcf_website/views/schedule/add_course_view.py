"""Add course to schedule from course flow."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ...models import Course
from ...schedule.add_course import (
    build_schedule_add_options,
    handle_add_course_post,
    schedule_add_modal_context,
)
from ...schedule.services import (
    resolve_builder_semester,
    schedule_page_url,
    schedules_for_user,
)
from ...utils import safe_next_url
from .json_helpers import (
    accepts_schedule_json,
    is_schedule_add_modal_get,
    schedule_json_fail,
    schedule_json_redirect,
)


@login_required
def schedule_add_course(  # pylint: disable=too-many-locals,too-many-return-statements
    request, course_id
):
    """Add a course to a schedule from the course flow."""
    course = get_object_or_404(Course, id=course_id)
    active_semester = resolve_builder_semester(request, request.user)
    schedules = schedules_for_user(request.user, active_semester)
    lecture_options, other_options = (
        build_schedule_add_options(course, active_semester)
        if active_semester
        else ([], [])
    )

    selected_schedule_id = request.POST.get("schedule_id") or request.GET.get(
        "schedule", ""
    )
    selected_options = request.POST.getlist("selection")

    if selected_schedule_id:
        schedule_builder_url = schedule_page_url(schedule_id=selected_schedule_id)
        fallback_url = schedule_builder_url
    else:
        schedule_builder_url = schedule_page_url(
            semester_id=active_semester.pk if active_semester else None
        )
        fallback_url = schedule_builder_url
    next_url = safe_next_url(request, fallback_url)

    page_state = {
        "active_semester": active_semester,
        "lecture_options": lecture_options,
        "other_options": other_options,
        "schedules": schedules,
        "selected_schedule_id": selected_schedule_id,
        "selected_options": selected_options,
        "fallback_course_url": fallback_url,
        "next_url": next_url,
        "schedule_builder_url": schedule_builder_url,
    }
    page_ctx = schedule_add_modal_context(course, page_state)

    if request.method == "POST":
        want_json = accepts_schedule_json(request)
        success_response = handle_add_course_post(
            request,
            course,
            selected_schedule_id,
            selected_options,
        )
        if success_response is not None:
            if want_json:
                loc = success_response.get("Location")
                redirect_to = loc or "/"
                return schedule_json_redirect(request, redirect_to)
            return success_response
        if want_json:
            return schedule_json_fail(
                request,
                status=400,
                fallback_message="Request failed.",
            )
        return redirect(safe_next_url(request, next_url))

    if is_schedule_add_modal_get(request):
        return render(
            request,
            "site/schedule/partials/_schedule_add_course_modal.html",
            page_ctx,
        )

    dest = request.GET.get("next")
    if dest:
        return redirect(safe_next_url(request, dest))
    return redirect(
        safe_next_url(
            request,
            reverse(
                "course",
                args=[course.subdepartment.mnemonic, course.number],
            ),
        )
    )

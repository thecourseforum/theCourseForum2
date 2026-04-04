"""Schedule CRUD and scheduled-course removal."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from ...models import Schedule, ScheduledCourse
from ...schedule.forms import ScheduleForm
from ...schedule.services import (
    resolve_builder_semester,
    schedule_page_url,
    schedule_visible_q,
)
from ...utils import safe_next_url
from .json_helpers import (
    accepts_schedule_json,
    schedule_json_error,
    schedule_json_fail,
    schedule_json_redirect,
)


@login_required
def new_schedule(request):
    """Take the user to the new schedule page."""
    if request.method == "POST":
        want_json = accepts_schedule_json(request)
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            semester = resolve_builder_semester(request, request.user)
            if semester is None:
                msg = "No semester data available."
                if want_json:
                    return schedule_json_error(request, msg, status=400)
                messages.error(request, msg)
                return redirect(safe_next_url(request, reverse("schedule")))
            schedule.semester = semester
            schedule.save()
            redirect_to = safe_next_url(
                request,
                schedule_page_url(schedule_id=schedule.pk),
            )
            messages.success(request, "Successfully created schedule!")
            if want_json:
                return schedule_json_redirect(request, redirect_to)
            return redirect(redirect_to)
        err = "Invalid schedule data."
        if form.errors:
            first = next(iter(form.errors.values()))
            if first:
                err = first[0]
        if want_json:
            return schedule_json_error(request, err, status=400)
        messages.error(request, err)
    return redirect(safe_next_url(request, reverse("schedule")))


@login_required
def delete_schedule(request):
    """Delete a schedule or multiple schedules."""
    redirect_to = safe_next_url(request, reverse("schedule"))
    if request.method != "POST":
        return redirect(redirect_to)

    schedule_ids = request.POST.getlist("selected_schedules")
    schedule_count = len(schedule_ids)

    deleted_count, _ = Schedule.objects.filter(
        id__in=schedule_ids, user=request.user
    ).delete()
    if deleted_count == 0:
        messages.error(request, "No schedules were deleted.")
        if accepts_schedule_json(request):
            return schedule_json_fail(
                request,
                status=400,
                fallback_message="No schedules were deleted.",
            )
        return redirect(redirect_to)

    extra_courses = deleted_count - schedule_count
    messages.success(
        request,
        f"Successfully deleted {schedule_count} schedules and {extra_courses} courses",
    )
    return schedule_json_redirect(request, redirect_to)


@login_required
def duplicate_schedule(request, schedule_id):
    """Duplicate a schedule the user can see (owned or bookmarked) into a new owned schedule."""
    source = (
        Schedule.objects.filter(pk=schedule_id)
        .filter(schedule_visible_q(request.user))
        .first()
    )
    if source is None:
        raise Http404

    source_pk = source.pk
    old_name = source.name

    if source.user_id == request.user.id:
        source.pk = None
        source.name = "Copy of " + old_name
        source.share_token = None
        source.save()
        duplicated_schedule = source
    else:
        duplicated_schedule = Schedule.objects.create(
            user=request.user,
            semester=source.semester,
            name="Copy of " + old_name,
            share_token=None,
        )

    for course in ScheduledCourse.objects.filter(schedule_id=source_pk):
        ScheduledCourse.objects.create(
            schedule=duplicated_schedule,
            section=course.section,
            instructor=course.instructor,
            time=course.time,
            enrolled_units=course.enrolled_units,
        )

    messages.success(request, f"Successfully duplicated {old_name}")
    redirect_to = safe_next_url(
        request, schedule_page_url(schedule_id=duplicated_schedule.pk)
    )
    return schedule_json_redirect(request, redirect_to)


@login_required
def edit_schedule(request):
    """Edit a schedule based on a selected schedule, and the changes passed in."""
    if request.method != "POST":
        messages.error(request, f"Invalid request method: {request.method}")
        return redirect(safe_next_url(request, reverse("schedule")))

    schedule = get_object_or_404(
        Schedule, pk=request.POST["schedule_id"], user=request.user
    )
    updated_name = request.POST.get("schedule_name", "").strip()
    if updated_name and schedule.name != updated_name:
        schedule.name = updated_name
        schedule.save()

    deleted_courses = request.POST.getlist("removed_course_ids[]")
    if deleted_courses:
        ScheduledCourse.objects.filter(
            id__in=deleted_courses,
            schedule__user=request.user,
        ).delete()

    messages.success(request, f"Successfully made changes to {schedule.name}")
    return redirect(safe_next_url(request, reverse("schedule")))


@login_required
def remove_scheduled_course(request, scheduled_course_id):
    """Remove one scheduled course from the active user's schedule."""
    if request.method != "POST":
        return redirect(reverse("schedule"))

    scheduled_course = get_object_or_404(
        ScheduledCourse,
        id=scheduled_course_id,
        schedule__user=request.user,
    )
    schedule_id = scheduled_course.schedule_id
    course_label = (
        f"{scheduled_course.section.course.subdepartment.mnemonic} "
        f"{scheduled_course.section.course.number}"
    )
    scheduled_course.delete()
    messages.success(request, f"Removed {course_label} from your schedule.")

    redirect_to = safe_next_url(request, schedule_page_url(schedule_id=schedule_id))
    return schedule_json_redirect(request, redirect_to)

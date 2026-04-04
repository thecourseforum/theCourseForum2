"""Schedule builder main page."""

import uuid
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from ...models import Schedule, ScheduleBookmark
from ...schedule.calendar import (
    build_merged_weekly_calendar,
    build_weekly_calendar,
    scheduled_courses_for_calendar,
)
from ...schedule.services import (
    resolve_builder_semester,
    resolve_compare_schedule,
    schedule_builder_return_url,
    schedule_data_helper,
)
from ...utils import recent_semesters
from .json_helpers import (
    is_schedule_compare_pick_partial_request,
    is_schedule_grid_partial_request,
)


@login_required
def view_schedules(  # pylint: disable=too-many-locals,too-many-return-statements,too-many-branches,too-many-statements
    request,
):
    """Render schedule builder page."""
    add_shared = request.GET.get("add_shared")
    if add_shared and request.method == "GET":
        try:
            share_uuid = uuid.UUID(str(add_shared).strip())
        except (ValueError, TypeError, AttributeError):
            messages.error(request, "Invalid share link.")
            return redirect(reverse("schedule"))

        shared = (
            Schedule.objects.filter(share_token=share_uuid)
            .select_related("semester")
            .first()
        )
        if shared is None:
            messages.error(
                request,
                "This share link is invalid or sharing was turned off.",
            )
            return redirect(reverse("schedule"))

        if shared.user_id == request.user.id:
            messages.info(request, "This schedule is already yours.")
            shared_q = urlencode(
                {"semester": shared.semester_id, "schedule": shared.pk}
            )
            return redirect(f"{reverse('schedule')}?{shared_q}")

        ScheduleBookmark.objects.get_or_create(viewer=request.user, schedule=shared)
        messages.success(
            request,
            f'Added "{shared.name}" to your schedules for this term.',
        )
        bookmark_q = urlencode(
            {"semester": shared.semester_id, "schedule": shared.pk}
        )
        return redirect(f"{reverse('schedule')}?{bookmark_q}")

    active_semester = resolve_builder_semester(request, request.user)
    all_semesters = recent_semesters()
    semester_choices = [(sem.pk, str(sem)) for sem in all_semesters]
    semester_combo_selected = active_semester.pk if active_semester else ""
    schedule_context = schedule_data_helper(request, active_semester)
    schedules = list(schedule_context["schedules"])

    selected_schedule = None
    selected_schedule_data = None
    if schedules:
        wanted = request.GET.get("schedule")
        selected_schedule = (
            next((s for s in schedules if str(s.id) == wanted), None) or schedules[0]
        )
        selected_schedule_data = selected_schedule.get_schedule()

    selected_courses = selected_schedule_data[0] if selected_schedule_data else []
    calendar = build_weekly_calendar(selected_courses)

    raw_compare_param = request.GET.get("compare")
    compare_schedule = resolve_compare_schedule(
        request, request.user, selected_schedule, active_semester
    )
    if (
        compare_schedule is not None
        and selected_schedule is not None
        and compare_schedule.pk == selected_schedule.pk
    ):
        compare_schedule = None

    self_compare_skipped = (
        selected_schedule is not None
        and raw_compare_param not in (None, "")
        and str(raw_compare_param) == str(selected_schedule.pk)
    )

    if (
        raw_compare_param not in (None, "")
        and compare_schedule is None
        and not self_compare_skipped
    ):
        messages.warning(
            request,
            "That schedule could not be loaded for comparison "
            "(wrong term or invalid link).",
        )

    compare_courses: list = []
    compare_calendar = None
    merged_calendar = None
    show_overlap = request.GET.get("overlap") == "1"

    compare_schedule_stats = None
    if compare_schedule is not None:
        compare_courses = scheduled_courses_for_calendar(compare_schedule)
        compare_data = compare_schedule.get_schedule()
        compare_schedule_stats = {
            "credits": compare_data[1] if compare_data else 0,
            "rating": compare_data[2] if compare_data else 0,
            "gpa": compare_data[4] if compare_data else 0,
        }
        if show_overlap:
            if (
                selected_schedule is not None
                and compare_schedule.pk != selected_schedule.pk
            ):
                merged_calendar = build_merged_weekly_calendar(
                    selected_courses, compare_courses
                )
        if merged_calendar is None:
            compare_calendar = build_weekly_calendar(compare_courses)

    schedule_preserve_params = {}
    if compare_schedule is not None:
        if request.GET.get("compare"):
            schedule_preserve_params["compare"] = request.GET.get("compare")
        if show_overlap:
            schedule_preserve_params["overlap"] = "1"

    compare_nav = None
    if (
        compare_schedule is not None
        and selected_schedule is not None
        and active_semester is not None
    ):
        params = {
            "semester": str(active_semester.pk),
            "schedule": str(selected_schedule.pk),
            "compare": str(compare_schedule.pk),
        }
        base_schedule_url = reverse("schedule")
        overlap_params = {**params, "overlap": "1"}
        clear_params = {
            "semester": str(active_semester.pk),
            "schedule": str(selected_schedule.pk),
        }
        compare_nav = {
            "split_url": f"{base_schedule_url}?{urlencode(params)}",
            "overlap_url": f"{base_schedule_url}?{urlencode(overlap_params)}",
            "clear_url": f"{base_schedule_url}?{urlencode(clear_params)}",
        }

    compare_exit_url = None
    if selected_schedule is not None and active_semester is not None:
        exit_params = {
            "semester": str(active_semester.pk),
            "schedule": str(selected_schedule.pk),
        }
        compare_exit_url = f"{reverse('schedule')}?{urlencode(exit_params)}"

    schedule_context.update(
        {
            "active_semester": active_semester,
            "all_semesters": all_semesters,
            "semester_choices": semester_choices,
            "semester_combo_selected": semester_combo_selected,
            "selected_schedule": selected_schedule,
            "selected_courses": selected_courses,
            "selected_schedule_stats": {
                "credits": (selected_schedule_data[1] if selected_schedule_data else 0),
                "rating": (selected_schedule_data[2] if selected_schedule_data else 0),
                "gpa": (selected_schedule_data[4] if selected_schedule_data else 0),
            },
            "calendar": calendar,
            "compare_schedule": compare_schedule,
            "compare_courses": compare_courses,
            "compare_schedule_stats": compare_schedule_stats,
            "compare_calendar": compare_calendar,
            "merged_calendar": merged_calendar,
            "compare_overlap": show_overlap,
            "schedule_preserve_params": schedule_preserve_params,
            "compare_nav": compare_nav,
            "compare_exit_url": compare_exit_url,
            "schedule_builder_return_url": schedule_builder_return_url(request),
        }
    )

    if is_schedule_compare_pick_partial_request(request):
        if selected_schedule is None:
            return render(
                request,
                "site/schedule/partials/_schedule_compare_pick_modal_body.html",
                {"schedules": [], "selected_schedule": None},
            )
        return render(
            request,
            "site/schedule/partials/_schedule_compare_pick_modal_body.html",
            {
                "schedules": schedules,
                "selected_schedule": selected_schedule,
            },
        )

    if is_schedule_grid_partial_request(request):
        return render(
            request,
            "site/schedule/partials/_schedule_builder_grid.html",
            schedule_context,
        )

    return render(request, "site/schedule/schedule.html", schedule_context)

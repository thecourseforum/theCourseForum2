"""Schedule sharing and bookmarks."""

import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from ...models import Schedule, ScheduleBookmark
from ...utils import safe_next_url
from .json_helpers import (
    accepts_schedule_json,
    schedule_json_error,
    schedule_json_fail,
    schedule_json_redirect,
)


@login_required
@require_POST
def schedule_share(request):
    """Enable, regenerate, or disable the share link for one of the user's schedules."""
    raw_id = request.POST.get("schedule_id")
    default_redirect = reverse("schedule")
    try:
        sid = int(raw_id)
    except (TypeError, ValueError):
        return schedule_json_error(request, "Invalid schedule.")

    schedule = Schedule.objects.filter(pk=sid, user=request.user).first()
    if schedule is None:
        return schedule_json_error(
            request, "You do not have permission to change that schedule."
        )

    action = request.POST.get("action")

    if action == "disable":
        schedule.share_token = None
        schedule.save()
        messages.success(request, "Stopped sharing this schedule.")
    elif action == "regenerate":
        schedule.share_token = uuid.uuid4()
        schedule.save()
        messages.success(request, "Share link updated.")
    elif action == "enable":
        if schedule.share_token is None:
            schedule.share_token = uuid.uuid4()
            schedule.save()
        messages.success(request, "Sharing enabled.")
    else:
        return schedule_json_error(request, "Invalid sharing action.")

    redirect_to = safe_next_url(request, default_redirect)
    return schedule_json_redirect(request, redirect_to)


@login_required
@require_POST
def schedule_unbookmark(request):
    """Remove a bookmarked shared schedule from the viewer's sidebar (does not delete it)."""
    raw_id = request.POST.get("schedule_id")
    redirect_to = safe_next_url(request, reverse("schedule"))
    try:
        sid = int(raw_id)
    except (TypeError, ValueError):
        return schedule_json_error(request, "Invalid schedule.")

    deleted, _ = ScheduleBookmark.objects.filter(
        viewer=request.user, schedule_id=sid
    ).delete()
    if deleted:
        messages.success(request, "Removed shared schedule from your list.")
    else:
        messages.error(request, "That schedule was not in your shared list.")
        if accepts_schedule_json(request):
            return schedule_json_fail(
                request,
                status=400,
                fallback_message="That schedule was not in your shared list.",
            )
        return redirect(redirect_to)

    return schedule_json_redirect(request, redirect_to)

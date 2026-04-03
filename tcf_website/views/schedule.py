"""View pertaining to schedule creation/viewing."""

import logging
import re
import uuid
from datetime import datetime, time
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import (
    Course,
    Instructor,
    Schedule,
    ScheduleBookmark,
    ScheduledCourse,
    Section,
    SectionTime,
    Semester,
)
from ..utils import recent_semesters, safe_next_url

# pylint: disable=line-too-long
# pylint: disable=duplicate-code
# pylint: disable=no-else-return
# pylint: disable=consider-using-generator

logger = logging.getLogger(__name__)


def _is_schedule_grid_partial_request(request):
    """True when client requests the schedule builder grid HTML fragment only."""
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and request.GET.get("partial") == "grid"
    )


def _is_schedule_compare_pick_partial_request(request):
    """XHR fragment: list of schedules to compare with (modal body)."""
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and request.GET.get("partial") == "compare_pick"
    )


def _accepts_schedule_json(request) -> bool:
    """True when the client expects a JSON body (modal / fetch flows)."""
    accept = request.headers.get("Accept", "")
    return "application/json" in accept


def _is_schedule_add_modal_get(request) -> bool:
    return (
        request.method == "GET"
        and request.GET.get("partial") == "modal"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def _schedule_builder_return_url(request) -> str:
    """Canonical builder URL for form ``next=`` (drops ``partial`` from query)."""
    q = request.GET.copy()
    q.pop("partial", None)
    qs = q.urlencode()
    path = request.path
    return f"{path}?{qs}" if qs else path


def _schedule_messages_list(request) -> list[dict[str, str]]:
    """Consume pending Django messages and return JSON-serializable rows for async clients."""
    return [
        {"message": str(m.message), "tags": m.tags}
        for m in messages.get_messages(request)
    ]


def _schedule_json_error_text(msgs: list[dict[str, str]], fallback: str) -> str:
    last_any = None
    last_error = None
    for item in msgs:
        text = item["message"]
        tags = item["tags"]
        last_any = text
        if "error" in tags:
            last_error = text
    return last_error or last_any or fallback


def _schedule_json_redirect(request, redirect_to: str):
    if _accepts_schedule_json(request):
        payload: dict = {"ok": True, "redirect": redirect_to}
        msgs = _schedule_messages_list(request)
        if msgs:
            payload["messages"] = msgs
        return JsonResponse(payload)
    return redirect(redirect_to)


def _schedule_json_error(
    request, message: str, *, fallback_url: str | None = None, status: int = 400
):
    if _accepts_schedule_json(request):
        msgs = _schedule_messages_list(request)
        if not msgs:
            msgs = [{"message": message, "tags": "error"}]
        err = _schedule_json_error_text(msgs, message)
        return JsonResponse(
            {"ok": False, "error": err, "messages": msgs},
            status=status,
        )
    messages.error(request, message)
    dest = fallback_url if fallback_url is not None else reverse("schedule")
    return redirect(safe_next_url(request, dest))


def _schedule_json_fail(request, *, status: int = 400, fallback_message: str) -> JsonResponse:
    """JSON error after views used ``messages.*`` (consumes message storage)."""
    msgs = _schedule_messages_list(request)
    if not msgs:
        msgs = [{"message": fallback_message, "tags": "error"}]
    err = _schedule_json_error_text(msgs, fallback_message)
    return JsonResponse({"ok": False, "error": err, "messages": msgs}, status=status)


def _schedule_visible_q(user):
    """Schedules the user may open on /schedule (owned or bookmarked)."""
    return Q(user=user) | Q(viewer_bookmarks__viewer=user)


def _schedule_page_url(
    *, semester_id: int | None = None, schedule_id: int | str | None = None
) -> str:
    """Builder URL: prefer ?schedule= (row defines the term); else ?semester= for term-only views."""
    if schedule_id:
        return f"{reverse('schedule')}?{urlencode({'schedule': schedule_id})}"
    if semester_id is not None:
        return f"{reverse('schedule')}?{urlencode({'semester': semester_id})}"
    return reverse("schedule")


DAY_FIELDS = (
    ("MON", "Mon", "monday"),
    ("TUE", "Tue", "tuesday"),
    ("WED", "Wed", "wednesday"),
    ("THU", "Thu", "thursday"),
    ("FRI", "Fri", "friday"),
)
DAY_TOKEN_MAP = {
    "mo": "MON",
    "tu": "TUE",
    "we": "WED",
    "th": "THU",
    "fr": "FRI",
}
DAY_TOKEN_PATTERN = re.compile(r"(mo|tu|we|th|fr)", flags=re.IGNORECASE)
MEETING_BLOCK_PATTERN = re.compile(
    r"(?P<days>[A-Za-z]+)\s+(?P<start>\d{1,2}:\d{2}\s*[APMapm]{2})\s*-\s*(?P<end>\d{1,2}:\d{2}\s*[APMapm]{2})"
)


def _is_lecture_section(section_type: str | None) -> bool:
    """Return True when a section type should be treated as lecture."""
    if not section_type:
        return True
    normalized = section_type.strip().lower()
    return normalized.startswith("lec") or "lecture" in normalized


def _clock_to_minutes(raw_clock: str) -> int | None:
    """Convert clock string like '9:30am' into minutes from midnight."""
    if not raw_clock:
        return None
    try:
        parsed = datetime.strptime(raw_clock.replace(" ", "").upper(), "%I:%M%p")
    except ValueError:
        return None
    return (parsed.hour * 60) + parsed.minute


def _time_to_minutes(value: time) -> int:
    """Convert a Python time object into minutes from midnight."""
    return (value.hour * 60) + value.minute


def _parse_fallback_meeting_blocks(raw_times: str) -> list[tuple[str, int, int]]:
    """Parse serialized section_times string into day/time tuples."""
    if not raw_times:
        return []

    parsed_blocks: list[tuple[str, int, int]] = []
    for block in raw_times.split(","):
        stripped = block.strip()
        if not stripped:
            continue

        match = MEETING_BLOCK_PATTERN.search(stripped)
        if not match:
            continue

        start_minutes = _clock_to_minutes(match.group("start"))
        end_minutes = _clock_to_minutes(match.group("end"))
        if start_minutes is None or end_minutes is None or end_minutes <= start_minutes:
            continue

        day_tokens = DAY_TOKEN_PATTERN.findall(match.group("days"))
        for token in day_tokens:
            day_code = DAY_TOKEN_MAP.get(token.lower())
            if day_code:
                parsed_blocks.append((day_code, start_minutes, end_minutes))

    return parsed_blocks


def _section_time_rows_to_blocks(
    section_time_rows: list[SectionTime],
) -> list[tuple[str, int, int]]:
    """Convert SectionTime rows into day/time tuples."""
    blocks: list[tuple[str, int, int]] = []
    for section_time in section_time_rows:
        start_minutes = _time_to_minutes(section_time.start_time)
        end_minutes = _time_to_minutes(section_time.end_time)
        if end_minutes <= start_minutes:
            continue
        for day_code, _, day_field in DAY_FIELDS:
            if getattr(section_time, day_field):
                blocks.append((day_code, start_minutes, end_minutes))
    return blocks


def _format_minutes(minutes: int) -> str:
    """Render minutes from midnight into 12-hour clock text."""
    hour = minutes // 60
    minute = minutes % 60
    suffix = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    if minute:
        return f"{hour_12}:{minute:02d} {suffix}"
    return f"{hour_12} {suffix}"


def _empty_weekly_calendar() -> dict:
    """Return empty calendar payload structure."""
    return {
        "columns": [
            {"code": code, "label": label, "events": []}
            for code, label, _ in DAY_FIELDS
        ],
        "time_labels": [],
        "slot_markers": [],
    }


def _build_section_time_map(section_ids: set[int]) -> dict[int, list[SectionTime]]:
    """Build map of section_id -> section time rows."""
    if not section_ids:
        return {}

    section_time_map: dict[int, list[SectionTime]] = {
        section_id: [] for section_id in section_ids
    }
    for section_time in SectionTime.objects.filter(section_id__in=section_ids):
        section_time_map.setdefault(section_time.section_id, []).append(section_time)
    return section_time_map


def _meeting_blocks_for_schedule_course(
    schedule_course: ScheduledCourse,
    section_time_map: dict[int, list[SectionTime]],
) -> list[tuple[str, int, int]]:
    """Return meeting blocks for one scheduled course."""
    section_rows = section_time_map.get(schedule_course.section_id, [])
    meeting_blocks = _section_time_rows_to_blocks(section_rows)
    if meeting_blocks:
        return meeting_blocks
    return _parse_fallback_meeting_blocks(
        schedule_course.time or schedule_course.section.section_times
    )


def _schedule_course_title(schedule_course: ScheduledCourse) -> str:
    """Return display title for a scheduled course."""
    return getattr(
        schedule_course,
        "title",
        f"{schedule_course.section.course.subdepartment.mnemonic} "
        f"{schedule_course.section.course.number}",
    )


def _schedule_course_instructor_name(schedule_course: ScheduledCourse) -> str:
    """Return display name for a scheduled course instructor."""
    if schedule_course.instructor.full_name:
        return schedule_course.instructor.full_name
    return f"{schedule_course.instructor.first_name} {schedule_course.instructor.last_name}".strip()


def _event_payloads_for_course(
    schedule_course: ScheduledCourse,
    meeting_blocks: list[tuple[str, int, int]],
    *,
    extra_class: str = "",
) -> list[dict]:
    """Build event payloads for one scheduled course."""
    if not meeting_blocks:
        return []

    section = schedule_course.section
    common_payload = {
        "title": _schedule_course_title(schedule_course),
        "subtitle": _schedule_course_instructor_name(schedule_course),
        "meta": f"Section {section.sis_section_number}",
        "tone": ((section.course_id % 6) + 1),
        "href": reverse(
            "course_instructor",
            args=[section.course_id, schedule_course.instructor_id],
        ),
        "extra_class": extra_class,
    }

    events = []
    for day_code, start_minutes, end_minutes in meeting_blocks:
        events.append(
            {
                "day_code": day_code,
                "start_minutes": start_minutes,
                "end_minutes": end_minutes,
                "start_label": _format_minutes(start_minutes),
                "end_label": _format_minutes(end_minutes),
                **common_payload,
            }
        )
    return events


def _weekly_events(
    schedule_courses: list[ScheduledCourse],
    section_time_map: dict[int, list[SectionTime]],
    *,
    extra_class: str = "",
) -> list[dict]:
    """Build all calendar events for schedule courses."""
    events: list[dict] = []
    for schedule_course in schedule_courses:
        meeting_blocks = _meeting_blocks_for_schedule_course(
            schedule_course,
            section_time_map,
        )
        events.extend(
            _event_payloads_for_course(
                schedule_course, meeting_blocks, extra_class=extra_class
            )
        )
    return events


def _calendar_window(events: list[dict]) -> tuple[int, int]:
    """Return calendar window start/end minutes."""
    earliest_start = min(event["start_minutes"] for event in events)
    latest_end = max(event["end_minutes"] for event in events)
    start_minutes = max(7 * 60, min(8 * 60, (earliest_start // 60) * 60))
    end_minutes = min(22 * 60, max(18 * 60, ((latest_end + 59) // 60) * 60))
    if end_minutes <= start_minutes:
        end_minutes = start_minutes + 60
    return start_minutes, end_minutes


def _apply_event_geometry(
    events: list[dict], start_minutes: int, end_minutes: int
) -> None:
    """Mutate event payloads with layout geometry fields."""
    total_minutes = end_minutes - start_minutes
    for event in events:
        clamped_start = max(start_minutes, min(end_minutes, event["start_minutes"]))
        clamped_end = max(clamped_start, min(end_minutes, event["end_minutes"]))
        event["top_pct"] = ((clamped_start - start_minutes) / total_minutes) * 100
        event["height_pct"] = max(
            4.0,
            ((clamped_end - clamped_start) / total_minutes) * 100,
        )


def _calendar_columns(events: list[dict]) -> list[dict]:
    """Group and sort events by day."""
    columns = []
    for day_code, day_label, _ in DAY_FIELDS:
        day_events = sorted(
            [event for event in events if event["day_code"] == day_code],
            key=lambda item: (item["start_minutes"], item["end_minutes"]),
        )
        columns.append({"code": day_code, "label": day_label, "events": day_events})
    return columns


def _build_weekly_calendar(schedule_courses: list[ScheduledCourse]) -> dict:
    """Build normalized weekly calendar payload for calendar component."""
    if not schedule_courses:
        return _empty_weekly_calendar()

    section_ids = {course.section_id for course in schedule_courses}
    section_time_map = _build_section_time_map(section_ids)
    events = _weekly_events(schedule_courses, section_time_map)

    if not events:
        return _empty_weekly_calendar()

    start_minutes, end_minutes = _calendar_window(events)
    _apply_event_geometry(events, start_minutes, end_minutes)

    columns = _calendar_columns(events)
    slot_count = max(1, (end_minutes - start_minutes) // 60)
    time_labels = [
        _format_minutes(start_minutes + (hour * 60)) for hour in range(slot_count + 1)
    ]

    return {
        "columns": columns,
        "time_labels": time_labels,
        "slot_markers": list(range(slot_count)),
    }


def _build_merged_weekly_calendar(
    primary_courses: list[ScheduledCourse],
    secondary_courses: list[ScheduledCourse],
) -> dict:
    """Single grid with two schedules; secondary events get a distinct style class."""
    if not primary_courses and not secondary_courses:
        return _empty_weekly_calendar()

    section_ids = {c.section_id for c in primary_courses} | {
        c.section_id for c in secondary_courses
    }
    section_time_map = _build_section_time_map(section_ids)
    events = _weekly_events(primary_courses, section_time_map, extra_class="")
    events.extend(
        _weekly_events(
            secondary_courses,
            section_time_map,
            extra_class="weekly-calendar__event--compare-b",
        )
    )

    if not events:
        return _empty_weekly_calendar()

    start_minutes, end_minutes = _calendar_window(events)
    _apply_event_geometry(events, start_minutes, end_minutes)

    columns = _calendar_columns(events)
    slot_count = max(1, (end_minutes - start_minutes) // 60)
    time_labels = [
        _format_minutes(start_minutes + (hour * 60)) for hour in range(slot_count + 1)
    ]

    return {
        "columns": columns,
        "time_labels": time_labels,
        "slot_markers": list(range(slot_count)),
    }


def _scheduled_courses_for_calendar(schedule: Schedule) -> list:
    """Scheduled course rows for lists and calendar (same as Schedule.get_schedule()[0])."""
    return schedule.get_scheduled_courses()


def _resolve_compare_schedule(
    request,
    user,
    selected_schedule: Schedule | None,
    active_semester: Semester | None,
) -> Schedule | None:
    """Load a schedule to compare with from ?compare= pk (any visible schedule)."""
    if active_semester is None:
        return None

    semester_id = (
        selected_schedule.semester_id
        if selected_schedule is not None
        else active_semester.pk
    )

    raw_compare = request.GET.get("compare")
    if raw_compare is None or raw_compare == "":
        return None
    try:
        pk = int(raw_compare)
    except (TypeError, ValueError):
        return None
    return (
        Schedule.objects.filter(pk=pk, semester_id=semester_id)
        .filter(_schedule_visible_q(user))
        .select_related("user")
        .first()
    )


def _existing_schedule_blocks(schedule: Schedule) -> list[tuple[str, int, int]]:
    """Return meeting blocks for all existing courses in a schedule."""
    existing_courses = list(
        ScheduledCourse.objects.filter(schedule=schedule).select_related("section")
    )
    if not existing_courses:
        return []

    section_ids = {course.section_id for course in existing_courses}
    section_time_map = _build_section_time_map(section_ids)

    existing_blocks: list[tuple[str, int, int]] = []
    for existing_course in existing_courses:
        existing_blocks.extend(
            _meeting_blocks_for_schedule_course(existing_course, section_time_map)
        )
    return existing_blocks


def _has_schedule_conflict(
    schedule: Schedule,
    candidate_blocks: list[tuple[str, int, int]],
) -> bool:
    """Return True if candidate meeting blocks conflict with schedule contents."""
    if not candidate_blocks:
        return False

    existing_blocks = _existing_schedule_blocks(schedule)
    if not existing_blocks:
        return False

    for candidate_day, candidate_start, candidate_end in candidate_blocks:
        for existing_day, existing_start, existing_end in existing_blocks:
            if candidate_day != existing_day:
                continue
            if candidate_start < existing_end and candidate_end > existing_start:
                return True

    return False


class ScheduleForm(forms.ModelForm):
    """
    Django form for interacting with a schedule
    """

    name = forms.CharField(max_length=100)

    class Meta:
        model = Schedule
        fields = ["name"]


def resolve_builder_semester(request, user) -> Semester | None:
    """Pick builder term: explicit semester wins, then schedule id, else latest.

    The term combo sends ?semester= together with hidden ?schedule=. That schedule id
    may still point at the previous term until the client syncs; inferring the term
    from schedule would ignore the user's new semester and show the wrong courses.
    """
    raw_sem = request.GET.get("semester") or request.POST.get("semester")
    if raw_sem:
        sem = Semester.objects.filter(pk=raw_sem).first()
        if sem is not None:
            return sem

    raw_sched = request.GET.get("schedule") or request.POST.get("schedule_id")
    if raw_sched:
        try:
            sched = (
                Schedule.objects.filter(pk=int(raw_sched))
                .filter(_schedule_visible_q(user))
                .select_related("semester")
                .first()
            )
            if sched:
                return sched.semester
        except (TypeError, ValueError):
            pass

    return Semester.latest()


def schedules_for_user(user, semester: Semester | None):
    """Owned and bookmarked schedules for one term, with courses prefetched."""
    if semester is None:
        return Schedule.objects.none()
    return (
        Schedule.objects.filter(_schedule_visible_q(user), semester=semester)
        .distinct()
        .order_by("name")
        .select_related("user")
        .prefetch_related(
            Prefetch(
                "scheduledcourse_set",
                queryset=ScheduledCourse.objects.select_related(
                    "section", "instructor"
                ),
            )
        )
    )


def schedule_data_helper(request, semester: Semester | None):
    """Schedule list and per-schedule aggregates for the schedule builder."""
    schedules = schedules_for_user(request.user, semester)
    courses_context = {}
    ratings_context = {}
    difficulty_context = {}
    credits_context = {}
    gpa_context = {}

    for s in schedules:
        s_data = s.get_schedule()
        courses_context[s.id] = s_data[0]
        credits_context[s.id] = s_data[1]
        ratings_context[s.id] = s_data[2]
        difficulty_context[s.id] = s_data[3]
        gpa_context[s.id] = s_data[4]

    ret = {
        "schedules": schedules,
        "courses": courses_context,
        "ratings": ratings_context,
        "difficulty": difficulty_context,
        "credits": credits_context,
        "schedules_gpa": gpa_context,
    }

    return ret


@login_required
def view_schedules(request):
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
            return redirect(
                f"{reverse('schedule')}?{urlencode({'semester': shared.semester_id, 'schedule': shared.pk})}"
            )

        ScheduleBookmark.objects.get_or_create(
            viewer=request.user, schedule=shared
        )
        messages.success(
            request,
            f'Added "{shared.name}" to your schedules for this term.',
        )
        return redirect(
            f"{reverse('schedule')}?{urlencode({'semester': shared.semester_id, 'schedule': shared.pk})}"
        )

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
    calendar = _build_weekly_calendar(selected_courses)

    raw_compare_param = request.GET.get("compare")
    compare_schedule = _resolve_compare_schedule(
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
        compare_courses = _scheduled_courses_for_calendar(compare_schedule)
        compare_data = compare_schedule.get_schedule()
        compare_schedule_stats = {
            "credits": compare_data[1] if compare_data else 0,
            "rating": compare_data[2] if compare_data else 0,
            "gpa": compare_data[4] if compare_data else 0,
        }
        if show_overlap:
            if selected_schedule is not None and compare_schedule.pk != selected_schedule.pk:
                merged_calendar = _build_merged_weekly_calendar(
                    selected_courses, compare_courses
                )
        if merged_calendar is None:
            compare_calendar = _build_weekly_calendar(compare_courses)

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
        compare_nav = {
            "split_url": f"{reverse('schedule')}?{urlencode(params)}",
            "overlap_url": f"{reverse('schedule')}?{urlencode({**params, 'overlap': '1'})}",
            "clear_url": f"{reverse('schedule')}?{urlencode({'semester': str(active_semester.pk), 'schedule': str(selected_schedule.pk)})}",
        }

    compare_exit_url = None
    if selected_schedule is not None and active_semester is not None:
        compare_exit_url = (
            f"{reverse('schedule')}?"
            f"{urlencode({'semester': str(active_semester.pk), 'schedule': str(selected_schedule.pk)})}"
        )

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
            "schedule_builder_return_url": _schedule_builder_return_url(request),
        }
    )

    if _is_schedule_compare_pick_partial_request(request):
        if selected_schedule is None:
            return render(
                request,
                "site/partials/_schedule_compare_pick_modal_body.html",
                {"schedules": [], "selected_schedule": None},
            )
        return render(
            request,
            "site/partials/_schedule_compare_pick_modal_body.html",
            {
                "schedules": schedules,
                "selected_schedule": selected_schedule,
            },
        )

    if _is_schedule_grid_partial_request(request):
        return render(
            request,
            "site/partials/_schedule_builder_grid.html",
            schedule_context,
        )

    return render(request, "site/pages/schedule.html", schedule_context)


@login_required
def new_schedule(request):
    """
    Take the user to the new schedule page.
    """
    if request.method == "POST":
        want_json = _accepts_schedule_json(request)
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            semester = resolve_builder_semester(request, request.user)
            if semester is None:
                msg = "No semester data available."
                if want_json:
                    return _schedule_json_error(request, msg, status=400)
                messages.error(request, msg)
                return redirect(safe_next_url(request, reverse("schedule")))
            schedule.semester = semester
            schedule.save()
            redirect_to = safe_next_url(
                request,
                _schedule_page_url(schedule_id=schedule.pk),
            )
            messages.success(request, "Successfully created schedule!")
            if want_json:
                return _schedule_json_redirect(request, redirect_to)
            return redirect(redirect_to)
        err = "Invalid schedule data."
        if form.errors:
            first = next(iter(form.errors.values()))
            if first:
                err = first[0]
        if want_json:
            return _schedule_json_error(request, err, status=400)
        messages.error(request, err)
    return redirect(safe_next_url(request, reverse("schedule")))


@login_required
def delete_schedule(request):
    """
    Delete a schedule or multiple schedules.
    """
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
        if _accepts_schedule_json(request):
            return _schedule_json_fail(
                request,
                status=400,
                fallback_message="No schedules were deleted.",
            )
        return redirect(redirect_to)

    messages.success(
        request,
        f"Successfully deleted {schedule_count} schedules and {deleted_count - schedule_count} courses",
    )
    return _schedule_json_redirect(request, redirect_to)


@login_required
def duplicate_schedule(request, schedule_id):
    """
    Duplicate a schedule the user can see (owned or bookmarked) into a new owned schedule.
    """
    source = (
        Schedule.objects.filter(pk=schedule_id)
        .filter(_schedule_visible_q(request.user))
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
        new_schedule = source
    else:
        new_schedule = Schedule.objects.create(
            user=request.user,
            semester=source.semester,
            name="Copy of " + old_name,
            share_token=None,
        )

    for course in ScheduledCourse.objects.filter(schedule_id=source_pk):
        ScheduledCourse.objects.create(
            schedule=new_schedule,
            section=course.section,
            instructor=course.instructor,
            time=course.time,
            enrolled_units=course.enrolled_units,
        )

    messages.success(request, f"Successfully duplicated {old_name}")
    redirect_to = safe_next_url(
        request, _schedule_page_url(schedule_id=new_schedule.pk)
    )
    return _schedule_json_redirect(request, redirect_to)


@login_required
@require_POST
def schedule_share(request):
    """Enable, regenerate, or disable the share link for one of the user's schedules."""
    raw_id = request.POST.get("schedule_id")
    default_redirect = reverse("schedule")
    try:
        sid = int(raw_id)
    except (TypeError, ValueError):
        return _schedule_json_error(request, "Invalid schedule.")

    schedule = Schedule.objects.filter(pk=sid, user=request.user).first()
    if schedule is None:
        return _schedule_json_error(
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
        return _schedule_json_error(request, "Invalid sharing action.")

    redirect_to = safe_next_url(request, default_redirect)
    return _schedule_json_redirect(request, redirect_to)


@login_required
@require_POST
def schedule_unbookmark(request):
    """Remove a bookmarked shared schedule from the viewer's sidebar (does not delete it)."""
    raw_id = request.POST.get("schedule_id")
    redirect_to = safe_next_url(request, reverse("schedule"))
    try:
        sid = int(raw_id)
    except (TypeError, ValueError):
        return _schedule_json_error(request, "Invalid schedule.")

    deleted, _ = ScheduleBookmark.objects.filter(
        viewer=request.user, schedule_id=sid
    ).delete()
    if deleted:
        messages.success(request, "Removed shared schedule from your list.")
    else:
        messages.error(request, "That schedule was not in your shared list.")
        if _accepts_schedule_json(request):
            return _schedule_json_fail(
                request,
                status=400,
                fallback_message="That schedule was not in your shared list.",
            )
        return redirect(redirect_to)

    return _schedule_json_redirect(request, redirect_to)


@login_required
def edit_schedule(request):
    """
    Edit a schedule based on a selected schedule, and the changes passed in.
    """
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

    redirect_to = safe_next_url(
        request, _schedule_page_url(schedule_id=schedule_id)
    )
    return _schedule_json_redirect(request, redirect_to)


# Credits: users pick hours only on this add form; enrolled_units is stored and not edited later.


def _append_schedule_add_option(
    bucket: list[dict],
    section: Section,
    instructor: Instructor,
    display_name: str,
    section_time: str,
) -> None:
    """One row per section/instructor; variable sections get a credits dropdown (add flow only)."""
    if section.is_variable_credit:
        credit_options = [
            {"value": str(c), "selected": c == section.units_max}
            for c in range(section.units_min, section.units_max + 1)
        ]
    else:
        credit_options = []

    bucket.append(
        {
            "value": f"{section.id}:{instructor.id}",
            "section_id": section.id,
            "instructor_id": instructor.id,
            "section_number": section.sis_section_number,
            "section_type": section.section_type or "Lecture",
            "section_units": section.units,
            "variable_credit": section.is_variable_credit,
            "credit_options": credit_options,
            "section_time": section_time,
            "instructor_name": display_name,
        }
    )


def _build_schedule_add_options(
    course: Course, term_semester: Semester
) -> tuple[list[dict], list[dict]]:
    """Build lecture and non-lecture options for the add-course form."""
    lecture_options = []
    other_options = []
    sections = (
        Section.objects.filter(course=course, semester=term_semester)
        .prefetch_related("instructors")
        .order_by("sis_section_number")
    )
    for section in sections:
        section_time = (section.section_times or "").rstrip(",")
        for instructor in section.instructors.all():
            if instructor.hidden:
                continue
            display_name = (
                instructor.full_name
                if instructor.full_name
                else f"{instructor.first_name} {instructor.last_name}".strip()
            )
            target = (
                lecture_options
                if _is_lecture_section(section.section_type)
                else other_options
            )
            _append_schedule_add_option(
                target, section, instructor, display_name, section_time
            )
    return lecture_options, other_options


def _parse_schedule_add_selection(
    selected_option: str,
) -> tuple[int | None, int | None, str | None]:
    """Parse one section selection from POST data."""
    if not selected_option:
        return None, None, "Choose at least one section to add."

    parts = selected_option.strip().split(":")
    if len(parts) != 2:
        return None, None, "Invalid section selection."

    try:
        section_id = int(parts[0])
        instructor_id = int(parts[1])
    except (TypeError, ValueError):
        return None, None, "Invalid section selection."

    return section_id, instructor_id, None


def _schedule_add_success_redirect(request, schedule: Schedule):
    """Return success redirect response for schedule add flow."""
    return redirect(safe_next_url(request, _schedule_page_url(schedule_id=schedule.pk)))


def _candidate_blocks_for_section(section: Section) -> list[tuple[str, int, int]]:
    """Return meeting blocks for one section."""
    candidate_blocks = _section_time_rows_to_blocks(list(section.sectiontime_set.all()))
    if not candidate_blocks:
        candidate_blocks = _parse_fallback_meeting_blocks(section.section_times)
    return candidate_blocks


def _blocks_conflict(
    existing_blocks: list[tuple[str, int, int]],
    candidate_blocks: list[tuple[str, int, int]],
) -> bool:
    """Return True when any block in two sets overlaps."""
    for existing_day, existing_start, existing_end in existing_blocks:
        for candidate_day, candidate_start, candidate_end in candidate_blocks:
            if existing_day != candidate_day:
                continue
            if candidate_start < existing_end and candidate_end > existing_start:
                return True
    return False


def _resolve_schedule_add_request(
    request,
    selected_schedule_id: str,
    selected_options: list[str],
):
    """Validate request-level schedule add inputs once per submit."""
    if not selected_options:
        return "Choose at least one section to add."
    if not selected_schedule_id:
        return "Choose a schedule first."

    schedule = Schedule.objects.filter(
        id=selected_schedule_id, user=request.user
    ).first()
    if schedule is None:
        return "Invalid schedule selection."

    return schedule, list(dict.fromkeys(selected_options))


def _add_course_to_schedule(
    request,
    schedule: Schedule,
    resolved_selection: tuple[Section, Instructor, int],
    existing_blocks: list[tuple[str, int, int]],
) -> bool:
    """Attempt to add one selected section and emit user-facing messages."""
    section, instructor, enrolled_units = resolved_selection
    if ScheduledCourse.objects.filter(
        schedule=schedule, section=section, instructor=instructor
    ).exists():
        messages.info(
            request,
            f"Section {section.sis_section_number} is already in this schedule.",
        )
        return False

    candidate_blocks = _candidate_blocks_for_section(section)
    if _blocks_conflict(existing_blocks, candidate_blocks):
        messages.error(
            request,
            f"Section {section.sis_section_number} conflicts with another meeting in the selected schedule.",
        )
        return False

    ScheduledCourse.objects.create(
        schedule=schedule,
        section=section,
        instructor=instructor,
        time=(section.section_times or "").rstrip(","),
        enrolled_units=enrolled_units,
    )
    existing_blocks.extend(candidate_blocks)
    return True


def _enrolled_units_from_schedule_add_post(
    request, section: Section, section_id: int, instructor_id: int
):
    """Parse credit hours from POST for variable-credit sections; (units, None) or (None, error)."""
    if section.units_min >= section.units_max:
        return section.units_min, None

    raw = request.POST.get(f"enrolled_units_{section_id}_{instructor_id}", "").strip()
    if not raw:
        return None, "Choose how many credits to take for this section."
    try:
        units = int(raw)
    except ValueError:
        return None, "Invalid credit value."
    if units < section.units_min or units > section.units_max:
        return None, "Credits are outside the range for this section."
    return units, None


def _resolve_schedule_add_post(
    request,
    course: Course,
    schedule: Schedule,
    selected_option: str,
):
    """Validate one selected section; return (section, instructor, units) or error message."""
    section_id, instructor_id, err = _parse_schedule_add_selection(selected_option)
    section = instructor = None
    enrolled_units = None

    if not err:
        section = Section.objects.filter(
            id=section_id,
            course=course,
            semester_id=schedule.semester_id,
        ).first()
        if section is None:
            err = "Invalid section selection."

    if not err:
        instructor = Instructor.objects.filter(id=instructor_id, hidden=False).first()
        if instructor is None:
            err = "Invalid instructor selection."
        elif not section.instructors.filter(id=instructor.id).exists():
            err = "The selected instructor does not teach that section."

    if not err:
        enrolled_units, credit_err = _enrolled_units_from_schedule_add_post(
            request, section, section_id, instructor_id
        )
        err = credit_err

    if err:
        return err
    return section, instructor, enrolled_units


def _handle_schedule_add_post(
    request,
    course: Course,
    selected_schedule_id: str,
    selected_options: list[str],
):
    """Handle POST submission for schedule add flow."""
    resolved_request = _resolve_schedule_add_request(
        request, selected_schedule_id, selected_options
    )
    if isinstance(resolved_request, str):
        messages.error(request, resolved_request)
        return None

    schedule, unique_options = resolved_request
    existing_blocks = _existing_schedule_blocks(schedule)
    with transaction.atomic():
        for selected_option in unique_options:
            resolved = _resolve_schedule_add_post(
                request, course, schedule, selected_option
            )
            if isinstance(resolved, str):
                messages.error(request, resolved)
                transaction.set_rollback(True)
                return None

            if not _add_course_to_schedule(
                request,
                schedule,
                resolved,
                existing_blocks,
            ):
                transaction.set_rollback(True)
                return None
    course_label = f"{course.subdepartment.mnemonic} {course.number}"
    messages.success(request, f"Successfully added {course_label} to schedule.")
    return _schedule_add_success_redirect(request, schedule)


def _schedule_add_modal_context(course: Course, page_state: dict) -> dict:
    """Template context for the add-to-schedule modal partial only."""
    return {
        "course": course,
        "active_semester": page_state["active_semester"],
        "lecture_options": page_state["lecture_options"],
        "other_options": page_state["other_options"],
        "schedules": page_state["schedules"],
        "selected_schedule_id": (
            str(page_state["selected_schedule_id"])
            if page_state["selected_schedule_id"]
            else ""
        ),
        "selected_options": page_state["selected_options"],
        "default_next_url": page_state["fallback_course_url"],
        "next_url": page_state["next_url"],
        "schedule_builder_url": page_state["schedule_builder_url"],
    }


@login_required
def schedule_add_course(request, course_id):
    """Add a course to a schedule from the course flow."""
    course = get_object_or_404(Course, id=course_id)
    active_semester = resolve_builder_semester(request, request.user)
    schedules = schedules_for_user(request.user, active_semester)
    lecture_options, other_options = (
        _build_schedule_add_options(course, active_semester)
        if active_semester
        else ([], [])
    )

    selected_schedule_id = request.POST.get("schedule_id") or request.GET.get(
        "schedule", ""
    )
    selected_options = request.POST.getlist("selection")

    if selected_schedule_id:
        schedule_builder_url = _schedule_page_url(schedule_id=selected_schedule_id)
        fallback_url = schedule_builder_url
    else:
        schedule_builder_url = _schedule_page_url(
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
    page_ctx = _schedule_add_modal_context(course, page_state)

    if request.method == "POST":
        want_json = _accepts_schedule_json(request)
        success_response = _handle_schedule_add_post(
            request,
            course,
            selected_schedule_id,
            selected_options,
        )
        if success_response is not None:
            if want_json:
                loc = success_response.get("Location")
                redirect_to = loc or "/"
                return _schedule_json_redirect(request, redirect_to)
            return success_response
        if want_json:
            return _schedule_json_fail(
                request,
                status=400,
                fallback_message="Request failed.",
            )
        return redirect(safe_next_url(request, next_url))

    if _is_schedule_add_modal_get(request):
        return render(
            request,
            "site/partials/_schedule_add_course_modal.html",
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

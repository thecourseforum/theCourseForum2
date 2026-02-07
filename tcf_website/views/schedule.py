"""View pertaining to schedule creation/viewing."""

import logging
import re
from datetime import datetime, time
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from ..models import (
    Course,
    Instructor,
    Schedule,
    ScheduledCourse,
    Section,
    SectionTime,
    Semester,
)

# pylint: disable=line-too-long
# pylint: disable=duplicate-code
# pylint: disable=no-else-return
# pylint: disable=consider-using-generator

logger = logging.getLogger(__name__)


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


def _safe_next_url(request, default_url: str) -> str:
    """Return validated next URL when present, otherwise default."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default_url


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


def _build_weekly_calendar(schedule_courses: list[ScheduledCourse]) -> dict:
    """Build normalized weekly calendar payload for calendar component."""
    if not schedule_courses:
        return {
            "columns": [{"code": code, "label": label, "events": []} for code, label, _ in DAY_FIELDS],
            "time_labels": [],
            "slot_markers": [],
        }

    section_ids = {course.section_id for course in schedule_courses}
    section_time_map: dict[int, list[SectionTime]] = {section_id: [] for section_id in section_ids}
    for section_time in SectionTime.objects.filter(section_id__in=section_ids):
        section_time_map.setdefault(section_time.section_id, []).append(section_time)

    events = []
    for schedule_course in schedule_courses:
        section_rows = section_time_map.get(schedule_course.section_id, [])
        meeting_blocks = _section_time_rows_to_blocks(section_rows)
        if not meeting_blocks:
            meeting_blocks = _parse_fallback_meeting_blocks(
                schedule_course.time or schedule_course.section.section_times
            )

        course_code = getattr(
            schedule_course,
            "title",
            f"{schedule_course.section.course.subdepartment.mnemonic} {schedule_course.section.course.number}",
        )
        instructor_name = (
            schedule_course.instructor.full_name
            if schedule_course.instructor.full_name
            else f"{schedule_course.instructor.first_name} {schedule_course.instructor.last_name}".strip()
        )
        section_label = f"Section {schedule_course.section.sis_section_number}"

        for day_code, start_minutes, end_minutes in meeting_blocks:
            events.append(
                {
                    "day_code": day_code,
                    "start_minutes": start_minutes,
                    "end_minutes": end_minutes,
                    "start_label": _format_minutes(start_minutes),
                    "end_label": _format_minutes(end_minutes),
                    "title": course_code,
                    "subtitle": instructor_name,
                    "meta": section_label,
                    "tone": ((schedule_course.section.course_id % 6) + 1),
                    "href": reverse(
                        "course_instructor",
                        args=[schedule_course.section.course_id, schedule_course.instructor_id],
                    ),
                }
            )

    if not events:
        return {
            "columns": [{"code": code, "label": label, "events": []} for code, label, _ in DAY_FIELDS],
            "time_labels": [],
            "slot_markers": [],
        }

    earliest_start = min(event["start_minutes"] for event in events)
    latest_end = max(event["end_minutes"] for event in events)
    start_minutes = max(7 * 60, min(8 * 60, (earliest_start // 60) * 60))
    end_minutes = min(22 * 60, max(18 * 60, ((latest_end + 59) // 60) * 60))
    if end_minutes <= start_minutes:
        end_minutes = start_minutes + 60

    total_minutes = end_minutes - start_minutes
    for event in events:
        clamped_start = max(start_minutes, min(end_minutes, event["start_minutes"]))
        clamped_end = max(clamped_start, min(end_minutes, event["end_minutes"]))
        event["top_pct"] = ((clamped_start - start_minutes) / total_minutes) * 100
        event["height_pct"] = max(4.0, ((clamped_end - clamped_start) / total_minutes) * 100)

    columns = []
    for day_code, day_label, _ in DAY_FIELDS:
        day_events = sorted(
            [event for event in events if event["day_code"] == day_code],
            key=lambda item: (item["start_minutes"], item["end_minutes"]),
        )
        columns.append({"code": day_code, "label": day_label, "events": day_events})

    slot_count = max(1, (end_minutes - start_minutes) // 60)
    time_labels = [_format_minutes(start_minutes + (hour * 60)) for hour in range(slot_count + 1)]

    return {
        "columns": columns,
        "time_labels": time_labels,
        "slot_markers": list(range(slot_count)),
    }


def _has_schedule_conflict(
    schedule: Schedule,
    candidate_blocks: list[tuple[str, int, int]],
) -> bool:
    """Return True if candidate meeting blocks conflict with schedule contents."""
    if not candidate_blocks:
        return False

    existing_courses = list(
        ScheduledCourse.objects.filter(schedule=schedule).select_related("section")
    )
    if not existing_courses:
        return False

    existing_section_ids = {course.section_id for course in existing_courses}
    existing_time_map: dict[int, list[SectionTime]] = {section_id: [] for section_id in existing_section_ids}
    for section_time in SectionTime.objects.filter(section_id__in=existing_section_ids):
        existing_time_map.setdefault(section_time.section_id, []).append(section_time)

    existing_blocks: list[tuple[str, int, int]] = []
    for existing_course in existing_courses:
        section_rows = existing_time_map.get(existing_course.section_id, [])
        blocks = _section_time_rows_to_blocks(section_rows)
        if not blocks:
            blocks = _parse_fallback_meeting_blocks(
                existing_course.time or existing_course.section.section_times
            )
        existing_blocks.extend(blocks)

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

    user_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=15)

    class Meta:
        model = Schedule
        fields = ["name", "user_id"]


def schedule_data_helper(request):
    """
    This helper method is for getting schedule data for a request.
    """
    schedules = Schedule.objects.filter(user=request.user).order_by("name").prefetch_related(
        Prefetch(
            "scheduledcourse_set",
            queryset=ScheduledCourse.objects.select_related("section", "instructor"),
        )
    )
    courses_context = (
        {}
    )  # contains the joined table for Schedule and ScheduledCourse models
    ratings_context = (
        {}
    )  # contains aggregated ratings for schedules, using the model's method
    difficulty_context = (
        {}
    )  # contains aggregated difficulty of schedules, using the model's method
    credits_context = (
        {}
    )  # contains the total credits of schedules, calculated in this view
    gpa_context = {}  # contains the weighted gpa, calculated in the model function

    # iterate over the schedules for this request in order to set up the context
    # this could also be optimized for the database by combining these queries
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
    schedule_context = schedule_data_helper(request)
    schedules = list(schedule_context["schedules"])

    selected_schedule = None
    selected_schedule_data = None
    selected_schedule_id = request.GET.get("schedule")
    if schedules:
        if selected_schedule_id:
            selected_schedule = next(
                (schedule for schedule in schedules if str(schedule.id) == selected_schedule_id),
                None,
            )
        if selected_schedule is None:
            selected_schedule = schedules[0]
        selected_schedule_data = selected_schedule.get_schedule()

    selected_courses = selected_schedule_data[0] if selected_schedule_data else []
    calendar = _build_weekly_calendar(selected_courses)

    schedule_context.update(
        {
            "selected_schedule": selected_schedule,
            "selected_courses": selected_courses,
            "selected_schedule_stats": {
                "credits": (selected_schedule_data[1] if selected_schedule_data else 0),
                "rating": (selected_schedule_data[2] if selected_schedule_data else 0),
                "gpa": (selected_schedule_data[4] if selected_schedule_data else 0),
            },
            "calendar": calendar,
            "new_schedule_user_id": request.user.id,
        }
    )

    return render(request, "site/pages/schedule.html", schedule_context)


@login_required
def new_schedule(request):
    """
    Take the user to the new schedule page.
    """
    if request.method == "POST":
        # Handle saving the schedule
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            if schedule.user is None:
                messages.error(request, "There was an error")
                return redirect(_safe_next_url(request, reverse("schedule")))
            schedule.save()
            messages.success(request, "Successfully created schedule!")
        else:
            messages.error(request, "Invalid schedule data.")
    return redirect(_safe_next_url(request, reverse("schedule")))


@login_required
def delete_schedule(request):
    """
    Delete a schedule or multiple schedules.
    """
    # we use POST since forms don't support the DELETE method
    if request.method == "POST":
        # Retrieve IDs from POST data
        schedule_ids = request.POST.getlist("selected_schedules")
        schedule_count = len(schedule_ids)

        # Perform bulk delete
        deleted_count, _ = Schedule.objects.filter(
            id__in=schedule_ids, user=request.user
        ).delete()
        if deleted_count == 0:
            messages.error(request, "No schedules were deleted.")
        else:
            messages.success(
                request,
                f"Successfully deleted {schedule_count} schedules and {deleted_count - schedule_count} courses",
            )
    return redirect(_safe_next_url(request, reverse("schedule")))


@login_required
def duplicate_schedule(request, schedule_id):
    """
    Duplicate a schedule given a schedule id in the request.
    """
    schedule = get_object_or_404(Schedule, pk=schedule_id, user=request.user)
    schedule.pk = None  # reset the key so it will be recreated when it's saved
    old_name = schedule.name
    schedule.name = "Copy of " + old_name
    schedule.save()

    courses = ScheduledCourse.objects.filter(schedule_id=schedule_id)

    for course in courses:
        # loop through all courses and add them to the new schedule
        course.pk = None
        course.schedule = schedule
        course.save()

    messages.success(request, f"Successfully duplicated {old_name}")
    return redirect(_safe_next_url(request, reverse("schedule")))


@login_required
def edit_schedule(request):
    """
    Edit a schedule based on a selected schedule, and the changes passed in.
    """
    if request.method != "POST":
        messages.error(request, f"Invalid request method: {request.method}")
        return redirect(_safe_next_url(request, reverse("schedule")))

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
    return redirect(_safe_next_url(request, reverse("schedule")))


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

    default_url = f"{reverse('schedule')}?{urlencode({'schedule': schedule_id})}"
    return redirect(_safe_next_url(request, default_url))


@login_required
def schedule_add_course(request, course_id):
    """Add a course to a schedule from the course flow."""
    course = get_object_or_404(Course, id=course_id)
    latest_semester = Semester.latest()
    schedules = Schedule.objects.filter(user=request.user).order_by("name")

    lecture_options = []
    other_options = []
    sections = (
        Section.objects.filter(course=course, semester=latest_semester)
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
            option = {
                "value": f"{section.id}:{instructor.id}",
                "section_id": section.id,
                "instructor_id": instructor.id,
                "section_number": section.sis_section_number,
                "section_type": section.section_type or "Lecture",
                "section_units": section.units,
                "section_time": section_time,
                "instructor_name": display_name,
            }
            if _is_lecture_section(section.section_type):
                lecture_options.append(option)
            else:
                other_options.append(option)

    selected_schedule_id = request.POST.get("schedule_id") or request.GET.get("schedule", "")
    selected_option = request.POST.get("selection", "")

    fallback_course_url = reverse(
        "course",
        args=[course.subdepartment.mnemonic, course.number],
    )
    next_url = _safe_next_url(request, fallback_course_url)

    if request.method == "POST":
        if not selected_schedule_id:
            messages.error(request, "Choose a schedule first.")
        elif not selected_option:
            messages.error(request, "Choose a section to add.")
        else:
            schedule = None
            try:
                section_id_raw, instructor_id_raw = selected_option.split(":")
                section_id = int(section_id_raw)
                instructor_id = int(instructor_id_raw)
                schedule_id = int(selected_schedule_id)
            except (TypeError, ValueError):
                messages.error(request, "Invalid section selection.")
            else:
                schedule = Schedule.objects.filter(
                    id=schedule_id,
                    user=request.user,
                ).first()
                if schedule is None:
                    messages.error(request, "Invalid schedule selection.")
                else:
                    section = Section.objects.filter(
                        id=section_id,
                        course=course,
                        semester=latest_semester,
                    ).first()
                    if section is None:
                        messages.error(request, "Invalid section selection.")
                    else:
                        instructor = Instructor.objects.filter(
                            id=instructor_id,
                            hidden=False,
                        ).first()
                        if instructor is None:
                            messages.error(request, "Invalid instructor selection.")
                        elif not section.instructors.filter(id=instructor.id).exists():
                            messages.error(
                                request,
                                "The selected instructor does not teach that section.",
                            )
                        elif ScheduledCourse.objects.filter(
                            schedule=schedule,
                            section=section,
                            instructor=instructor,
                        ).exists():
                            messages.info(
                                request,
                                "That section is already in this schedule.",
                            )
                        else:
                            candidate_blocks = _section_time_rows_to_blocks(
                                list(section.sectiontime_set.all())
                            )
                            if not candidate_blocks:
                                candidate_blocks = _parse_fallback_meeting_blocks(
                                    section.section_times
                                )

                            if _has_schedule_conflict(schedule, candidate_blocks):
                                messages.error(
                                    request,
                                    (
                                        "This section conflicts with another meeting "
                                        "in the selected schedule."
                                    ),
                                )
                            else:
                                ScheduledCourse.objects.create(
                                    schedule=schedule,
                                    section=section,
                                    instructor=instructor,
                                    time=(section.section_times or "").rstrip(","),
                                )
                                messages.success(
                                    request, "Successfully added course to schedule."
                                )

                                default_url = (
                                    f"{reverse('schedule')}?"
                                    f"{urlencode({'schedule': schedule.id})}"
                                )
                                return redirect(_safe_next_url(request, default_url))

    dept = course.subdepartment.department
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.id]), False),
        (
            course.code(),
            reverse("course", args=[course.subdepartment.mnemonic, course.number]),
            False,
        ),
        ("Add to Schedule", None, True),
    ]

    return render(
        request,
        "site/pages/schedule_add_course.html",
        {
            "course": course,
            "breadcrumbs": breadcrumbs,
            "lecture_options": lecture_options,
            "other_options": other_options,
            "schedules": schedules,
            "selected_schedule_id": str(selected_schedule_id) if selected_schedule_id else "",
            "selected_option": selected_option,
            "new_schedule_user_id": request.user.id,
            "default_next_url": fallback_course_url,
            "next_url": next_url,
        },
    )

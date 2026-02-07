"""View pertaining to schedule creation/viewing."""

import json
import logging
import re
from datetime import datetime, time
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models import Avg, Case, CharField, Max, Prefetch, Q, Value, When
from django.db.models.functions import Cast, Concat
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
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


def load_secs_helper(course, latest_semester):
    """Helper function for course_view and for a view in schedule.py"""
    instructors = (
        Instructor.objects.filter(section__course=course, hidden=False)
        .distinct()
        .annotate(
            gpa=Avg(
                "courseinstructorgrade__average",
                filter=Q(courseinstructorgrade__course=course),
            ),
            difficulty=Avg("review__difficulty", filter=Q(review__course=course)),
            rating=(
                Avg("review__instructor_rating", filter=Q(review__course=course))
                + Avg("review__enjoyability", filter=Q(review__course=course))
                + Avg("review__recommendability", filter=Q(review__course=course))
            )
            / 3,
            semester_last_taught=Max(
                "section__semester", filter=Q(section__course=course)
            ),
            # ArrayAgg:
            # https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/aggregates/#arrayagg
            section_times=ArrayAgg(
                Case(
                    When(
                        section__semester=latest_semester,
                        then="section__section_times",
                    ),
                    output_field=CharField(),
                ),
                distinct=True,
            ),
            section_nums=ArrayAgg(
                Case(
                    When(
                        section__semester=latest_semester,
                        then="section__sis_section_number",
                    ),
                    output_field=CharField(),
                ),
                distinct=True,
            ),
            section_details=ArrayAgg(
                # this is to get sections in this format: section.id /%
                # section.section_num /% section.time /% section_type
                Concat(
                    Cast("section__id", CharField()),
                    Value(" /% "),
                    Case(
                        When(
                            section__semester=latest_semester,
                            then=Cast("section__sis_section_number", CharField()),
                        ),
                        default=Value(""),
                        output_field=CharField(),
                    ),
                    Value(" /% "),
                    "section__section_times",
                    Value(" /% "),
                    "section__section_type",
                    Value(" /% "),
                    "section__units",
                    output_field=CharField(),
                ),
                distinct=True,
            ),
        )
    )

    # Note: Refactor pls

    for i in instructors:
        if i.section_times[0] is not None and i.section_nums[0] is not None:
            i.times = {}
            for idx, _ in enumerate(i.section_times):
                if i.section_times[idx] is not None and i.section_nums[idx] is not None:
                    i.times[str(i.section_nums[idx])] = i.section_times[idx][:-1].split(
                        ","
                    )
        if None in i.section_nums:
            i.section_nums.remove(None)

    return instructors


class ScheduleForm(forms.ModelForm):
    """
    Django form for interacting with a schedule
    """

    user_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=15)

    class Meta:
        model = Schedule
        fields = ["name", "user_id"]


class SectionForm(forms.ModelForm):
    """
    Django form for adding a course to a schedule
    """

    class Meta:
        model = ScheduledCourse
        fields = ["schedule", "section", "instructor", "time"]


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
def view_schedules_legacy(request):
    """
    Get all schedules, and the related courses, for a given user.
    """
    schedule_context = schedule_data_helper(request)

    # add an empty schedule form into the context
    # to be used in the create_schedule_modal
    form = ScheduleForm()
    schedule_context["form"] = form

    return render(request, "schedule/user_schedules.html", schedule_context)


@login_required
def view_select_schedules_modal(request, mode):
    """
    Get all schedules and display in the modal.
    """
    schedule_context = schedule_data_helper(request)

    if mode == "add_course":
        schedule_context["mode"] = mode
    else:
        schedule_context["mode"] = "edit_schedule"
    modal_content = render_to_string(
        "schedule/select_schedule_modal.html", schedule_context, request
    )

    return HttpResponse(modal_content)


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
                return render(request, "schedule/user_schedules.html", {"form": form})
            schedule.save()
            messages.success(request, "Successfully created schedule!")
    else:
        # if schedule isn't getting saved, then don't do anything
        # for part two of the this project, load the actual course builder page
        form = ScheduleForm()
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
def modal_load_editor(request):
    """
    Load the schedule editor modal with schedule data.
    """
    if request.method != "POST":
        messages.error(request, f"Invalid request method: {request.method}")
        return JsonResponse({"status": "Method Not Allowed"}, status=405)

    body_unicode = request.body.decode("utf-8")
    body = json.loads(body_unicode)
    schedule_id = body.get("schedule_id")

    if not schedule_id:
        messages.error(request, "Schedule ID is missing")
        return JsonResponse({"status": "Bad Request"}, status=400)

    try:
        schedule = Schedule.objects.get(pk=schedule_id, user=request.user)
    except Schedule.DoesNotExist:
        messages.error(request, "Schedule not found")
        return JsonResponse({"status": "Not Found"}, status=404)

    schedule_data = schedule.get_schedule()

    context = {
        "schedule": schedule,
        "schedule_courses": schedule_data[0],
        "schedule_credits": schedule_data[1],
        "schedule_ratings": schedule_data[2],
        "schedule_difficulty": schedule_data[3],
        "schedule_gpa": schedule_data[4],
    }
    return render(request, "schedule/schedule_editor.html", context)


@login_required
def edit_schedule(request):
    """
    Edit a schedule based on a selected schedule, and the changes passed in.
    """
    if request.method != "POST":
        messages.error(request, f"Invalid request method: {request.method}")
        return JsonResponse({"status": "Method Not Allowed"}, status=405)

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
def modal_load_sections(request):
    """
    Load the instructors and section times for a course, and the schedule, when adding to schedule from the modal.
    """
    # pylint: disable=too-many-locals
    if request.method != "POST":
        return JsonResponse({"status": "Method Not Allowed"}, status=405)

    body_unicode = request.body.decode("utf-8")
    body = json.loads(body_unicode)
    course_id = body["course_id"]
    schedule_id = body["schedule_id"]

    # get the course based off passed in course_id
    course = Course.objects.get(pk=course_id)
    latest_semester = Semester.latest()

    data = {}
    instructors = load_secs_helper(course, latest_semester).filter(
        semester_last_taught=latest_semester.id
    )

    for i in instructors:
        temp = {}
        data[i.id] = temp

        # decode the string in section_details and take skip strings without a time or section_id
        encoded_sections = [
            x.split(" /% ")
            for x in i.section_details
            if x.split(" /% ")[2] != "" and x.split(" /% ")[1] != ""
        ]

        # strip the traling comma
        for section in encoded_sections:
            if section[2].endswith(","):
                section[2] = section[2].rstrip(",")

        temp["sections"] = encoded_sections
        temp["name"] = i.first_name + " " + i.last_name
        temp["rating"] = i.rating
        temp["difficulty"] = i.difficulty
        temp["gpa"] = i.gpa

    schedule = get_object_or_404(Schedule, pk=schedule_id, user=request.user)
    schedule_data = schedule.get_schedule()
    context = {
        "instructors_data": data,
        "schedule": schedule,
        "schedule_courses": schedule_data[0],
        "schedule_credits": schedule_data[1],
        "schedule_ratings": schedule_data[2],
        "schedule_difficulty": schedule_data[3],
        "schedule_gpa": schedule_data[4],
    }
    return render(request, "schedule/schedule_with_sections.html", context)


@login_required
def schedule_add_course_legacy(request):
    """Add a course to a schedule, the request should be FormData for the SectionForm class."""

    if request.method == "POST":
        # Parse the JSON-encoded 'selected_course' field
        try:
            selected_course = json.loads(
                request.POST.get("selected_course", "{}")
            )  # Default to empty dict if not found
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )

        form_data = {
            "schedule": request.POST.get("schedule_id"),
            "instructor": int(selected_course.get("instructor")),
            "section": int(selected_course.get("section")),
            "time": selected_course.get("section_time"),
        }

        # make form object with our passed in data
        form = SectionForm(form_data)

        if form.is_valid():
            scheduled_course = form.save(commit=False)
            schedule = form.cleaned_data["schedule"]
            instructor = form.cleaned_data["instructor"]
            section = form.cleaned_data["section"]
            course_time = form.cleaned_data["time"]

            if schedule.user_id != request.user.id:
                return JsonResponse({"status": "error"}, status=403)

            candidate_blocks = _section_time_rows_to_blocks(list(section.sectiontime_set.all()))
            if not candidate_blocks:
                candidate_blocks = _parse_fallback_meeting_blocks(
                    course_time or section.section_times
                )
            if _has_schedule_conflict(schedule, candidate_blocks):
                messages.error(
                    request,
                    "This section conflicts with another meeting in the selected schedule.",
                )
                return JsonResponse({"status": "conflict"})

            if ScheduledCourse.objects.filter(
                schedule=schedule,
                section=section,
                instructor=instructor,
            ).exists():
                messages.info(request, "This section is already in the selected schedule.")
                return JsonResponse({"status": "duplicate"})

            scheduled_course.schedule = schedule
            scheduled_course.instructor = instructor
            scheduled_course.section = section
            scheduled_course.time = course_time
            scheduled_course.save()
        else:
            messages.error(request, "Invalid form data")
            return JsonResponse({"status": "error"}, status=400)

    messages.success(request, "Succesfully added course!")
    return JsonResponse({"status": "success"})


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

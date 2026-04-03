"""Weekly calendar payloads and meeting-block / conflict helpers for schedule builder."""

import re
from datetime import datetime, time

from django.urls import reverse

from ..models import ScheduledCourse, SectionTime

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


def is_lecture_section(section_type: str | None) -> bool:
    """Return True when a section type should be treated as lecture."""
    if not section_type:
        return True
    normalized = section_type.strip().lower()
    return normalized.startswith("lec") or "lecture" in normalized


def _clock_to_minutes(raw_clock: str) -> int | None:
    if not raw_clock:
        return None
    try:
        parsed = datetime.strptime(raw_clock.replace(" ", "").upper(), "%I:%M%p")
    except ValueError:
        return None
    return (parsed.hour * 60) + parsed.minute


def _time_to_minutes(value: time) -> int:
    return (value.hour * 60) + value.minute


def parse_fallback_meeting_blocks(raw_times: str) -> list[tuple[str, int, int]]:
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


def section_time_rows_to_blocks(
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
    hour = minutes // 60
    minute = minutes % 60
    suffix = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    if minute:
        return f"{hour_12}:{minute:02d} {suffix}"
    return f"{hour_12} {suffix}"


def empty_weekly_calendar() -> dict:
    return {
        "columns": [
            {"code": code, "label": label, "events": []}
            for code, label, _ in DAY_FIELDS
        ],
        "time_labels": [],
        "slot_markers": [],
    }


def _build_section_time_map(section_ids: set[int]) -> dict[int, list[SectionTime]]:
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
    section_rows = section_time_map.get(schedule_course.section_id, [])
    meeting_blocks = section_time_rows_to_blocks(section_rows)
    if meeting_blocks:
        return meeting_blocks
    return parse_fallback_meeting_blocks(
        schedule_course.time or schedule_course.section.section_times
    )


def _schedule_course_title(schedule_course: ScheduledCourse) -> str:
    return getattr(
        schedule_course,
        "title",
        f"{schedule_course.section.course.subdepartment.mnemonic} "
        f"{schedule_course.section.course.number}",
    )


def _schedule_course_instructor_name(schedule_course: ScheduledCourse) -> str:
    if schedule_course.instructor.full_name:
        return schedule_course.instructor.full_name
    return f"{schedule_course.instructor.first_name} {schedule_course.instructor.last_name}".strip()


def _event_payloads_for_course(
    schedule_course: ScheduledCourse,
    meeting_blocks: list[tuple[str, int, int]],
    *,
    extra_class: str = "",
) -> list[dict]:
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
    columns = []
    for day_code, day_label, _ in DAY_FIELDS:
        day_events = sorted(
            [event for event in events if event["day_code"] == day_code],
            key=lambda item: (item["start_minutes"], item["end_minutes"]),
        )
        columns.append({"code": day_code, "label": day_label, "events": day_events})
    return columns


def build_weekly_calendar(schedule_courses: list[ScheduledCourse]) -> dict:
    if not schedule_courses:
        return empty_weekly_calendar()

    section_ids = {course.section_id for course in schedule_courses}
    section_time_map = _build_section_time_map(section_ids)
    events = _weekly_events(schedule_courses, section_time_map)

    if not events:
        return empty_weekly_calendar()

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


def build_merged_weekly_calendar(
    primary_courses: list[ScheduledCourse],
    secondary_courses: list[ScheduledCourse],
) -> dict:
    if not primary_courses and not secondary_courses:
        return empty_weekly_calendar()

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
        return empty_weekly_calendar()

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


def scheduled_courses_for_calendar(schedule):
    """Scheduled course rows for lists and calendar (same as Schedule.get_schedule()[0])."""
    return schedule.get_scheduled_courses()


def existing_schedule_blocks(schedule) -> list[tuple[str, int, int]]:
    from ..models import ScheduledCourse

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


def has_schedule_conflict(
    schedule,
    candidate_blocks: list[tuple[str, int, int]],
) -> bool:
    if not candidate_blocks:
        return False

    blocks = existing_schedule_blocks(schedule)
    if not blocks:
        return False

    for candidate_day, candidate_start, candidate_end in candidate_blocks:
        for existing_day, existing_start, existing_end in blocks:
            if candidate_day != existing_day:
                continue
            if candidate_start < existing_end and candidate_end > existing_start:
                return True

    return False

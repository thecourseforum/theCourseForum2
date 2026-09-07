"""Add-course options, validation, conflict checks, and POST handling."""

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect

from ..models import Course, Instructor, Schedule, ScheduledCourse, Section
from ..utils import safe_next_url
from .calendar import (
    existing_schedule_blocks,
    is_lecture_section,
    parse_fallback_meeting_blocks,
    section_time_rows_to_blocks,
)
from .services import schedule_page_url


def append_schedule_add_option(
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


def build_schedule_add_options(
    course: Course, term_semester
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
                if is_lecture_section(section.section_type)
                else other_options
            )
            append_schedule_add_option(
                target, section, instructor, display_name, section_time
            )
    return lecture_options, other_options


def parse_schedule_add_selection(
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


def candidate_blocks_for_section(section: Section) -> list[tuple[str, int, int]]:
    """Return meeting blocks for one section."""
    candidate_blocks = section_time_rows_to_blocks(list(section.sectiontime_set.all()))
    if not candidate_blocks:
        candidate_blocks = parse_fallback_meeting_blocks(section.section_times)
    return candidate_blocks


def blocks_conflict(
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


def resolve_schedule_add_request(
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


def add_course_to_schedule(
    request,
    schedule,
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

    candidate_blocks = candidate_blocks_for_section(section)
    if blocks_conflict(existing_blocks, candidate_blocks):
        msg = (
            f"Section {section.sis_section_number} conflicts with another meeting "
            "in the selected schedule."
        )
        messages.error(request, msg)
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


def enrolled_units_from_schedule_add_post(
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


def resolve_schedule_add_post(
    request,
    course: Course,
    schedule,
    selected_option: str,
):
    """Validate one selected section; return (section, instructor, units) or error message."""
    section_id, instructor_id, err = parse_schedule_add_selection(selected_option)
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
        assert section is not None and instructor is not None
        assert section_id is not None and instructor_id is not None
        enrolled_units, credit_err = enrolled_units_from_schedule_add_post(
            request, section, section_id, instructor_id
        )
        err = credit_err

    if err:
        return err
    return section, instructor, enrolled_units


def schedule_add_success_redirect(request, schedule):
    """Return success redirect response for schedule add flow."""
    return redirect(safe_next_url(request, schedule_page_url(schedule_id=schedule.pk)))


def handle_add_course_post(
    request,
    course: Course,
    selected_schedule_id: str,
    selected_options: list[str],
):
    """Handle POST submission for schedule add flow. Returns HttpResponse or None on error."""
    resolved_request = resolve_schedule_add_request(
        request, selected_schedule_id, selected_options
    )
    if isinstance(resolved_request, str):
        messages.error(request, resolved_request)
        return None

    schedule, unique_options = resolved_request
    blocks = existing_schedule_blocks(schedule)
    with transaction.atomic():
        for selected_option in unique_options:
            resolved = resolve_schedule_add_post(
                request, course, schedule, selected_option
            )
            if isinstance(resolved, str):
                messages.error(request, resolved)
                transaction.set_rollback(True)
                return None

            if not add_course_to_schedule(
                request,
                schedule,
                resolved,
                blocks,
            ):
                transaction.set_rollback(True)
                return None
    course_label = f"{course.subdepartment.mnemonic} {course.number}"
    messages.success(request, f"Successfully added {course_label} to schedule.")
    return schedule_add_success_redirect(request, schedule)


def schedule_add_modal_context(course: Course, page_state: dict) -> dict:
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

"""
Module for fetching and updating section enrollment data asynchronously.
"""

# pylint: disable=unnecessary-lambda
import asyncio
from datetime import timedelta

import requests
from asgiref.sync import sync_to_async
from django.http import HttpResponseNotFound
from django.utils import timezone

from tcf_website.models import (
    Course,
    CourseEnrollment,
    Section,
    SectionEnrollment,
    Semester,
)

TIMEOUT = 10
MAX_WORKERS = 5


def build_sis_api_url(section):
    """Build the SIS API URL for a given section.

    Args:
        section: Section object to build URL for

    Returns:
        str: The complete SIS API URL
    """
    return (
        "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM."
        "H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
        f"?institution=UVA01&term={section.semester.number}&page=1&"
        f"class_nbr={section.sis_section_number}"
    )


def fetch_section_data(section):
    """Fetch enrollment data for a given section from the UVA SIS API."""
    url = build_sis_api_url(section)

    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if data and "classes" in data and data["classes"]:
            class_data = data["classes"][0]
            return {
                "enrollment_taken": class_data.get("enrollment_total", 0),
                "enrollment_limit": class_data.get("class_capacity", 0),
                "waitlist_taken": class_data.get("wait_tot", 0),
                "waitlist_limit": class_data.get("wait_cap", 0),
            }
    except requests.exceptions.RequestException as e:
        print(f"Network error while fetching section {section.sis_section_number}: {e}")
    except ValueError as e:
        print(f"JSON decoding error for section {section.sis_section_number}: {e}")
    # Returns empty dictionary when data for a class was not found
    return {}


async def update_enrollment_data(course_id):
    """Asynchronous function to update enrollment data."""
    course_exists = await sync_to_async(Course.objects.filter(id=course_id).exists)()
    if not course_exists:
        return HttpResponseNotFound("Course not found.")

    # Check if the course's enrollment data was updated within the last 2 hours
    enrollment_tracking, created = await sync_to_async(
        CourseEnrollment.objects.get_or_create
    )(course_id=course_id)
    if not created and timezone.now() - enrollment_tracking.last_update < timedelta(
        hours=2
    ):
        return  # Skip update if it was updated less than 2 hours ago
    course = await sync_to_async(Course.objects.get)(id=course_id)
    latest_semester = await sync_to_async(lambda: Semester.latest())()

    sections_queryset = Section.objects.filter(course=course, semester=latest_semester)
    sections = await sync_to_async(list)(sections_queryset)

    if not sections:
        return

    changed_sections = 0

    async def process_section(section):
        """Fetch and update enrollment data asynchronously."""
        nonlocal changed_sections
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, fetch_section_data, section)

        if data:
            was_changed = await sync_to_async(update_section_enrollment)(section, data)
            if was_changed:
                changed_sections += 1

    await asyncio.gather(*(process_section(section) for section in sections))

    # Update the last_update timestamp
    enrollment_tracking.last_update = timezone.now()
    await sync_to_async(enrollment_tracking.save)()


def update_section_enrollment(section, data):
    """Update SectionEnrollment only if the data has changed."""
    section_enrollment, _ = SectionEnrollment.objects.get_or_create(section=section)

    has_changes = any(
        [
            section_enrollment.enrollment_taken != data.get("enrollment_taken", 0),
            section_enrollment.enrollment_limit != data.get("enrollment_limit", 0),
            section_enrollment.waitlist_taken != data.get("waitlist_taken", 0),
            section_enrollment.waitlist_limit != data.get("waitlist_limit", 0),
        ]
    )

    if has_changes:
        section_enrollment.enrollment_taken = data.get("enrollment_taken", 0)
        section_enrollment.enrollment_limit = data.get("enrollment_limit", 0)
        section_enrollment.waitlist_taken = data.get("waitlist_taken", 0)
        section_enrollment.waitlist_limit = data.get("waitlist_limit", 0)
        section_enrollment.save()

    return has_changes

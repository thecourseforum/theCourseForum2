"""
Module for fetching and updating section enrollment data asynchronously.
"""

import sys
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.http import HttpResponseNotFound

from tcf_website.models import Section, SectionEnrollment, Semester, Course

if "test" in sys.argv:
    def update_enrollment_data(*args, **kwargs):
        """Mock function to disable enrollment update during tests."""
        return

    print("Skipping update_enrollment_data in tests.")
else:
    TIMEOUT = 10
    MAX_WORKERS = 5

    def fetch_section_data(section):
        """Fetch enrollment data for a given section from the UVA SIS API."""
        url = (
            "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM."
            "H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
            f"?institution=UVA01&term={section.semester.number}&page=1&"
            f"class_nbr={section.sis_section_number}"
        )

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

        return {}

    async def update_enrollment_data(course_id):
        """Asynchronous function to update enrollment data using ThreadPoolExecutor."""
        start_time = time.monotonic()

        if not await sync_to_async(Course.objects.filter(id=course_id).exists)():
            return HttpResponseNotFound("Course not found.")
        course = await sync_to_async(Course.objects.get)(id=course_id)
        latest_semester = await sync_to_async(Semester.latest)()
        sections = await sync_to_async(list)(
            Section.objects.filter(course=course, semester=latest_semester)
        )

        if not sections:
            print(f"No sections found for course {course.code()} in semester {latest_semester}.")
            return

        print(f"Starting async enrollment update for {len(sections)} sections...")

        async def process_section(section):
            """Fetch and update enrollment data asynchronously using ThreadPoolExecutor."""
            loop = asyncio.get_running_loop()

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                data = await loop.run_in_executor(executor, fetch_section_data, section)

            if data:
                await sync_to_async(update_section_enrollment)(section, data)
                print(f"Updated enrollment for section {section.sis_section_number}")

        await asyncio.gather(*(process_section(section) for section in sections))

        elapsed_time = time.monotonic() - start_time
        print(f"Enrollment update completed at {timezone.now()} "
              f"(Total time: {elapsed_time:.2f} seconds)")

    def update_section_enrollment(section, data):
        """Update SectionEnrollment safely within an async function."""
        section_enrollment, _ = SectionEnrollment.objects.get_or_create(section=section)
        section_enrollment.enrollment_taken = data.get("enrollment_taken", 0)
        section_enrollment.enrollment_limit = data.get("enrollment_limit", 0)
        section_enrollment.waitlist_taken = data.get("waitlist_taken", 0)
        section_enrollment.waitlist_limit = data.get("waitlist_limit", 0)
        section_enrollment.save()

        print(
            f"Updated section {section.sis_section_number} | "
            f"Enrollment: {section_enrollment.enrollment_taken}/"
            f"{section_enrollment.enrollment_limit} | "
            f"Waitlist: {section_enrollment.waitlist_taken}/"
            f"{section_enrollment.waitlist_limit}"
        )

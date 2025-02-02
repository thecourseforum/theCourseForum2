import asyncio
import logging
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async

from tcf_website.models import Section, SectionEnrollment, Semester, Course

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIMEOUT = 10
MAX_WORKERS = 10
CACHE_TIMEOUT = 30


async def update_enrollment_data(course_id):
    """Asynchronous function to update enrollment data using ThreadPoolExecutor."""
    start_time = time.monotonic()
    course = await sync_to_async(Course.objects.get)(id=course_id)
    latest_semester = await sync_to_async(Semester.latest)()
    sections = await sync_to_async(lambda: list(Section.objects.filter(course=course, semester=latest_semester)))()

    if not sections:
        logger.info(f"No sections found for course {course.code()} in semester {latest_semester}.")
        return

    logger.info(f"Starting async enrollment update for {len(sections)} sections...")

    cache.set(f"enrollment_update_{course_id}", "processing", CACHE_TIMEOUT)

    async def process_section(section):
        """Fetch and update enrollment data asynchronously using ThreadPoolExecutor."""
        loop = asyncio.get_running_loop()

        section_enrollment, _ = await sync_to_async(SectionEnrollment.objects.get_or_create)(section=section)
    
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            data = await loop.run_in_executor(executor, fetch_section_data, section)

        if data:
            await sync_to_async(update_section_enrollment)(section, data)
            logger.info(f"Updated enrollment for section {section.sis_section_number}")
            return
        else:
            logger.info(f"No data found for section {section.sis_section_number}")
            return

    tasks = [process_section(section) for section in sections]
    results = await asyncio.gather(*tasks)

    cache.set(f"enrollment_update_{course_id}", "done", CACHE_TIMEOUT)
    elapsed_time = time.monotonic() - start_time
    logger.info(f"Enrollment update completed at {timezone.now()} (Total time: {elapsed_time:.2f} seconds)")
    return results


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
        logger.error(f"Network error while fetching section {section.sis_section_number}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching section {section.sis_section_number}: {e}")

    return {}


def update_section_enrollment(section, data):
    """Sync function to update SectionEnrollment safely within an async function."""
    section_enrollment, created = SectionEnrollment.objects.get_or_create(section=section)
    section_enrollment.enrollment_taken = data.get('enrollment_taken', 0)
    section_enrollment.enrollment_limit = data.get('enrollment_limit', 0)
    section_enrollment.waitlist_taken = data.get('waitlist_taken', 0)
    section_enrollment.waitlist_limit = data.get('waitlist_limit', 0)

    logger.info(
        f"Updated section {section.sis_section_number} | "
        f"Enrollment: {section_enrollment.enrollment_taken}/{section_enrollment.enrollment_limit} | "
        f"Waitlist: {section_enrollment.waitlist_taken}/{section_enrollment.waitlist_limit}"
    )

    section_enrollment.save()

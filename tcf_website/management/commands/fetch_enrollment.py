"""
Fetch and save enrollment data from SIS API for the current semester.

Usage:
python manage.py fetch_enrollment
OR
docker exec -it tcf_django python manage.py fetch_enrollment
"""

import time
from concurrent.futures import ThreadPoolExecutor

import backoff
import requests
from django.core.management.base import BaseCommand
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from tcf_website.models import Section, SectionEnrollment, Semester

# Maximum time to wait for a response from the server
TIMEOUT = 30
# Number of concurrent workers for fetching data
MAX_WORKERS = 20
# Initial wait time for backoff (in seconds)
INITIAL_WAIT = 2
# Maximum number of retry attempts
MAX_TRIES = 8
# Kept larger than MAX_WORKERS to handle connection lifecycle issues
MAX_POOL_SIZE = 20 * 5

# Configure session with retry strategy and connection pooling
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(
    pool_connections=MAX_POOL_SIZE,
    pool_maxsize=MAX_POOL_SIZE,
    max_retries=retry_strategy,
)
session.mount("http://", adapter)
session.mount("https://", adapter)


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


def should_retry_request(exception):
    """Determine if we should retry the request based on the exception."""
    if isinstance(exception, requests.exceptions.RequestException):
        # Retry on rate limits (429) and connection errors
        if isinstance(exception, requests.exceptions.HTTPError):
            return exception.response.status_code == 429
        return True
    return False


@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=MAX_TRIES,
    giveup=lambda e: not should_retry_request(e),
    base=2,
    factor=INITIAL_WAIT,
)
def fetch_section_data(section):
    """Fetch enrollment data for a given section from the UVA SIS API.

    Args:
        section: Section object to fetch enrollment data for

    Returns:
        bool: True if successful, False otherwise
    """
    url = build_sis_api_url(section)

    try:
        # Fetch and validate response
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()

        # Update enrollment data if available
        if data and "classes" in data and data["classes"]:
            class_data = data["classes"][0]
            section_enrollment, _ = SectionEnrollment.objects.get_or_create(
                section=section
            )

            # Update enrollment and waitlist numbers
            section_enrollment.enrollment_taken = class_data.get("enrollment_total", 0)
            section_enrollment.enrollment_limit = class_data.get("class_capacity", 0)
            section_enrollment.waitlist_taken = class_data.get("wait_tot", 0)
            section_enrollment.waitlist_limit = class_data.get("wait_cap", 0)
            section_enrollment.save()

            return True

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 429:
            print(
                f"Rate limited while fetching section {section.sis_section_number}. Retrying..."
            )
            raise  # Re-raise to trigger backoff
        print(
            f"HTTP error while fetching section {section.sis_section_number}: {http_err}"
        )
    except requests.exceptions.RequestException as req_err:
        print(
            f"Network error while fetching section {section.sis_section_number}: {req_err}"
        )
        raise  # Re-raise to trigger backoff
    except ValueError as val_err:
        print(
            f"JSON decoding error for section {section.sis_section_number}: {val_err}"
        )
    except Exception as err:  # pylint: disable=broad-except
        print(f"Unexpected error for section {section.sis_section_number}: {err}")

    return False


class Command(BaseCommand):
    """Django management command to fetch enrollment data for all sections."""

    help = "Fetches current enrollment data for all sections in the latest semester"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--semester",
            type=str,
            help='Semester number (e.g., "1242" for Spring 2024). Defaults to latest semester.',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        start_time = time.time()

        # Use provided semester or get latest
        if options["semester"]:
            semester = Semester.objects.get(number=options["semester"])
        else:
            semester = Semester.latest()

        print(f"Fetching enrollment data for semester {semester}...")

        sections = Section.objects.filter(semester=semester)
        total_sections = sections.count()
        print(f"Found {total_sections} sections")

        # Process sections in parallel using ThreadPoolExecutor
        success_count = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            try:
                results = list(
                    tqdm(
                        executor.map(fetch_section_data, sections),
                        total=total_sections,
                        desc="Fetching enrollment",
                    )
                )
                success_count = sum(1 for r in results if r)
            except KeyboardInterrupt:
                print("\nProcess interrupted by user. Shutting down...")
                executor.shutdown(wait=False)
                return

        elapsed_time = time.time() - start_time
        print(f"\nSuccessfully updated {success_count}/{total_sections} sections")
        print(f"Total time: {elapsed_time:.2f} seconds")

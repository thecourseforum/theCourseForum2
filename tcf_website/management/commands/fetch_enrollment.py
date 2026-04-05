"""
Fetch enrollment data from UVA SIS API.

Usage:
    python manage.py fetch_enrollment
    python manage.py fetch_enrollment --semester 1268
"""

import time
from concurrent.futures import ThreadPoolExecutor

import requests
from django.core.management.base import BaseCommand
from tqdm import tqdm

from tcf_website.management.http import requests_session_with_pool_and_retries
from tcf_website.models import Section, Semester

API_URL = (
    "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/"
    "WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
)
TIMEOUT = 30
WORKERS = 15
ENROLLMENT_FIELDS = [
    "enrollment_taken",
    "enrollment_limit",
    "waitlist_taken",
    "waitlist_limit",
]


def create_session():
    """Single retry layer with exponential backoff (1s, 2s, 4s, 8s)."""
    return requests_session_with_pool_and_retries(
        workers=WORKERS,
        status_forcelist=[429, 500, 502, 503, 504],
    )


def fetch_one(session, term, section):
    """Fetch enrollment for a single section. Returns the section if
    updated, None otherwise. Never raises."""
    try:
        resp = session.get(
            API_URL,
            params={
                "institution": "UVA01",
                "term": term,
                "page": 1,
                "class_nbr": section.sis_section_number,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()

        # Server returns HTML login pages under load instead of 429s
        if "json" not in resp.headers.get("Content-Type", ""):
            return None

        data = resp.json()
        classes = data.get("classes")
        if not classes:
            return None

        cls = classes[0]
        section.enrollment_taken = cls.get("enrollment_total", 0)
        section.enrollment_limit = cls.get("class_capacity", 0)
        section.waitlist_taken = cls.get("wait_tot", 0)
        section.waitlist_limit = cls.get("wait_cap", 0)
        return section

    except (requests.RequestException, ValueError, KeyError):
        return None


class Command(BaseCommand):
    """Management command: bulk-fetch SIS enrollment for all sections in a semester."""

    help = "Fetch current enrollment data for all sections in a semester"

    def add_arguments(self, parser):
        parser.add_argument(
            "--semester", help='Semester number, e.g. "1268". Defaults to latest.'
        )

    def handle(self, *args, **options):
        start = time.time()

        semester = (
            Semester.objects.get(number=options["semester"])
            if options["semester"]
            else Semester.latest()
        )
        sections = list(Section.objects.filter(semester=semester))
        self.stdout.write(
            f"Fetching enrollment for {semester} ({len(sections)} sections)"
        )

        session = create_session()
        term = semester.number

        # ── Fetch all sections concurrently ──
        def _fetch(section):
            return fetch_one(session, term, section)

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            results = list(
                tqdm(
                    pool.map(_fetch, sections),
                    total=len(sections),
                    desc="Fetching",
                )
            )

        updated = [s for s in results if s is not None]
        failed_sections = [s for s, r in zip(sections, results) if r is None]

        # ── Retry failures once ──
        if failed_sections:
            self.stdout.write(f"Retrying {len(failed_sections)} failed sections...")
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                retries = list(
                    tqdm(
                        pool.map(_fetch, failed_sections),
                        total=len(failed_sections),
                        desc="Retrying",
                    )
                )
            updated.extend(s for s in retries if s is not None)

        # ── Single bulk DB write ──
        Section.objects.bulk_update(updated, ENROLLMENT_FIELDS, batch_size=500)

        elapsed = time.time() - start
        self.stdout.write(
            f"\nUpdated {len(updated)}/{len(sections)} sections in {elapsed:.1f}s"
        )

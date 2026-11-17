"""
Fetch enrollment data from UVA SIS.

Pages the term's class search once (sequentially, one page at a time), reusing
the whole-term paging from fetch_data. Each page already carries enrollment
counts, so a refresh is a few hundred page reads instead of one request per
section.

Usage:
    python manage.py fetch_enrollment
    python manage.py fetch_enrollment --semester 1268
"""

import time

import requests
from cachalot.api import invalidate
from django.core.management.base import BaseCommand, CommandError

from tcf_website.management.commands.fetch_data import (
    create_session,
    fetch_sis_courses,
)
from tcf_website.models import Section, Semester

ENROLLMENT_FIELDS = [
    "enrollment_taken",
    "enrollment_limit",
    "waitlist_taken",
    "waitlist_limit",
]
SIS_FIELD_MAP = {
    "enrollment_taken": "enrollment_total",
    "enrollment_limit": "class_capacity",
    "waitlist_taken": "wait_tot",
    "waitlist_limit": "wait_cap",
}


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def apply_record(section, record):
    """Set a section's enrollment fields from a SIS class record; returns the section."""
    for field, sis_key in SIS_FIELD_MAP.items():
        setattr(section, field, _as_int(record.get(sis_key)))
    return section


class Command(BaseCommand):
    """Management command: refresh SIS enrollment for all sections in a semester."""

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

        fetch_start = time.time()
        try:
            with create_session(term=semester.number) as session:
                self.stdout.write(
                    f"Session ready; paging SIS class search for term {semester.number}"
                )
                records = fetch_sis_courses(session)
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            raise CommandError(f"SIS fetch failed: {exc}") from exc

        self.stdout.write(
            f"Fetched {len(records)} SIS records in {time.time() - fetch_start:.1f}s"
        )

        if not records:
            raise CommandError("SIS returned no classes; existing data was kept.")

        by_class_nbr = {str(record["class_nbr"]): record for record in records}

        updated = [
            apply_record(section, by_class_nbr[str(section.sis_section_number)])
            for section in sections
            if str(section.sis_section_number) in by_class_nbr
        ]
        self.stdout.write(
            f"Matched {len(updated)}/{len(sections)} sections; writing to database"
        )

        Section.objects.bulk_update(updated, ENROLLMENT_FIELDS, batch_size=500)
        invalidate(Section)

        elapsed = time.time() - start
        self.stdout.write(
            f"\nUpdated {len(updated)}/{len(sections)} sections "
            f"from {len(by_class_nbr)} SIS records in {elapsed:.1f}s"
        )

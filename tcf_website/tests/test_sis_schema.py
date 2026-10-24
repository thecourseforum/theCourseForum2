"""Tests for the SIS section structure check that guards fetch_data."""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from tcf_website.management.commands.fetch_data import SECTION_MAPPING
from tcf_website.management.sis_schema import SECTION_FIELDS, validate_sis_courses

VALID_SECTION = {
    "class_nbr": 12345,
    "subject": "CS",
    "catalog_nbr": "2100",
    "class_section": "001",
    "component": "LEC",
    "units": "3",
    "descr": "Data Structures and Algorithms 1",
    "topic": "",
    "enrl_stat_descr": "Open",
    "enrollment_total": 100,
    "class_capacity": 200,
    "wait_tot": 0,
    "wait_cap": 50,
    "crse_attr_value": "",
    "crse_id": "000001",
    "crse_offer_nbr": 1,
    "instructors": [{"name": "Jane Doe"}],
    "meetings": [
        {
            "instructor": "Jane Doe",
            "days": "MoWe",
            "start_time": "14.00.00.000000",
            "end_time": "15.15.00.000000",
            "room": "Rice Hall 130",
            "start_dt": "08/26/2026",
            "end_dt": "12/08/2026",
        }
    ],
}


class ValidateSisCoursesTests(SimpleTestCase):
    """Structure check for raw SIS ClassSearch records."""

    def test_valid_section_passes(self):
        validate_sis_courses([VALID_SECTION])

    def test_schema_covers_every_mapped_csv_field(self):
        self.assertLessEqual(set(SECTION_MAPPING.values()), SECTION_FIELDS)

    def test_missing_section_field_fails(self):
        section = {k: v for k, v in VALID_SECTION.items() if k != "enrollment_total"}
        with self.assertRaisesRegex(ValueError, "12345.*missing enrollment_total"):
            validate_sis_courses([VALID_SECTION, section])

    def test_malformed_meeting_fails(self):
        section = VALID_SECTION | {"meetings": [{"days": "MoWe"}]}
        with self.assertRaisesRegex(ValueError, r"missing meetings\[0\]\.room"):
            validate_sis_courses([section])

    def test_non_list_instructors_fails(self):
        section = VALID_SECTION | {"instructors": "Jane Doe"}
        with self.assertRaisesRegex(ValueError, "instructors is not a list"):
            validate_sis_courses([section])

    def test_fetch_data_fails_without_writing_csv(self):
        section = {k: v for k, v in VALID_SECTION.items() if k != "meetings"}
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(
                "tcf_website.management.commands.fetch_data.fetch_sis_courses",
                return_value=[section],
            ),
        ):
            output = Path(tmp) / "courses.csv"
            with self.assertRaisesRegex(CommandError, "missing meetings"):
                call_command(
                    "fetch_data",
                    "2026_fall",
                    "--subjects",
                    "CS",
                    "--output",
                    str(output),
                    "--json",
                    "--no-progress",
                    stdout=StringIO(),
                )
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".json").exists())

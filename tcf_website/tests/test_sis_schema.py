"""Tests for the SIS structure checks that guard fetch_data."""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from tcf_website.management.commands.fetch_data import SECTION_MAPPING
from tcf_website.management.sis_schema import (
    SECTION_FIELDS,
    catalog_description,
    class_attributes,
    validate_sis_courses,
)

VALID_MEETING = {
    "instructor": "Jane Doe",
    "days": "MoWe",
    "start_time": "14.00.00.000000",
    "end_time": "15.15.00.000000",
    "room": "Rice Hall 130",
    "start_dt": "08/26/2026",
    "end_dt": "12/08/2026",
}
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
    "meetings": [VALID_MEETING],
}
VALID_DETAILS = {
    "section_info": {
        "catalog_descr": {"crse_catalog_description": "Lists, trees, and graphs."},
        "enrollment_information": {"class_attributes": "First Writing\nNo Cost"},
    }
}


def fake_sis(classes, details=VALID_DETAILS):
    """Stand in for request_sis_json: one search page, then the given ClassDetails."""

    def respond(session, endpoint, **params):
        if endpoint == "IScript_ClassSearch":
            return {"pageCount": 1, "classes": classes}
        return details

    return respond


class ValidateSisCoursesTests(SimpleTestCase):
    """Structure check for raw SIS ClassSearch records."""

    def test_valid_section_passes(self):
        validate_sis_courses([VALID_SECTION])

    def test_null_crse_attr_value_passes(self):
        validate_sis_courses([VALID_SECTION | {"crse_attr_value": None}])

    def test_schema_covers_every_mapped_csv_field(self):
        self.assertLessEqual(set(SECTION_MAPPING.values()), set(SECTION_FIELDS))

    def test_missing_section_field_fails(self):
        section = {
            k: v for k, v in VALID_SECTION.items() if k != "enrollment_total"
        } | {"class_nbr": 67890}
        with self.assertRaisesRegex(ValueError, "67890.*missing enrollment_total"):
            validate_sis_courses([VALID_SECTION, section])

    def test_malformed_meeting_fails(self):
        section = VALID_SECTION | {"meetings": [{"days": "MoWe"}]}
        with self.assertRaisesRegex(ValueError, r"missing meetings\[0\]\.room"):
            validate_sis_courses([section])

    def test_non_list_instructors_fails(self):
        section = VALID_SECTION | {"instructors": "Jane Doe"}
        with self.assertRaisesRegex(ValueError, "instructors has unexpected type str"):
            validate_sis_courses([section])

    def test_non_text_crse_attr_value_fails(self):
        section = VALID_SECTION | {"crse_attr_value": 42}
        with self.assertRaisesRegex(
            ValueError, "crse_attr_value has unexpected type int"
        ):
            validate_sis_courses([section])

    def test_non_text_meeting_instructor_fails(self):
        section = VALID_SECTION | {"meetings": [VALID_MEETING | {"instructor": None}]}
        with self.assertRaisesRegex(
            ValueError, r"meetings\[0\]\.instructor has unexpected type NoneType"
        ):
            validate_sis_courses([section])


class ClassDetailsTests(SimpleTestCase):
    """Structure check for SIS ClassDetails descriptions and attributes."""

    def test_returns_description(self):
        self.assertEqual(
            catalog_description(VALID_DETAILS, 12345), "Lists, trees, and graphs."
        )

    def test_empty_description_is_allowed(self):
        for text in (" ", None):
            details = {
                "section_info": {"catalog_descr": {"crse_catalog_description": text}}
            }
            self.assertEqual(catalog_description(details, 12345), "")

    def test_missing_description_field_fails(self):
        with self.assertRaisesRegex(ValueError, "12345.*missing catalog_descr"):
            catalog_description({"section_info": {}}, 12345)

    def test_non_text_description_fails(self):
        details = {"section_info": {"catalog_descr": {"crse_catalog_description": 7}}}
        with self.assertRaisesRegex(
            ValueError, "crse_catalog_description has unexpected type int"
        ):
            catalog_description(details, 12345)

    def test_returns_class_attributes(self):
        self.assertEqual(
            class_attributes(VALID_DETAILS, 12345), ["First Writing", "No Cost"]
        )


class FetchDataStructureTests(SimpleTestCase):
    """fetch_data stops without writing a CSV when SIS data has the wrong structure."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.output = Path(tmp.name) / "courses.csv"

    def fetch(self, sis, *options):
        with patch(
            "tcf_website.management.commands.fetch_data.request_sis_json",
            side_effect=sis,
        ):
            call_command(
                "fetch_data",
                "2026_fall",
                "--subjects",
                "CS",
                "--output",
                str(self.output),
                "--description-source",
                "sis",
                "--no-progress",
                *options,
                stdout=StringIO(),
            )

    def test_valid_data_writes_csv(self):
        self.fetch(fake_sis([VALID_SECTION | {"crse_attr_value": "NEW-CODE"}]))
        csv = self.output.read_text()
        self.assertIn("Lists, trees, and graphs.", csv)
        self.assertIn("First Writing", csv)

    def test_bad_section_fails_before_writing_files(self):
        section = {k: v for k, v in VALID_SECTION.items() if k != "class_nbr"}
        with self.assertRaisesRegex(CommandError, "missing class_nbr"):
            self.fetch(fake_sis([section]), "--json")
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_suffix(".json").exists())

    def test_bad_description_fails_without_writing_csv(self):
        with self.assertRaisesRegex(CommandError, "12345.*missing catalog_descr"):
            self.fetch(fake_sis([VALID_SECTION], {"section_info": {}}))
        self.assertFalse(self.output.exists())

    def test_bad_attributes_fail_without_writing_csv(self):
        section = VALID_SECTION | {"crse_attr_value": "NEW-CODE"}
        details = {"section_info": {"catalog_descr": {"crse_catalog_description": ""}}}
        with self.assertRaisesRegex(
            CommandError, "12345.*missing enrollment_information"
        ):
            self.fetch(fake_sis([section], details))
        self.assertFalse(self.output.exists())

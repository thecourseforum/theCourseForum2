"""Tests for enrollment data updates."""

from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase

from .test_utils import setup

COMMAND = "tcf_website.management.commands.fetch_enrollment"


class TestEnrollment(TestCase):
    """Test cases for enrollment data updates."""

    def setUp(self):
        """Set up test data."""
        setup(self)
        self.section = self.section_course
        self.section.enrollment_taken = 10
        self.section.enrollment_limit = 20
        self.section.waitlist_taken = 5
        self.section.waitlist_limit = 10
        self.section.save()

    def _run(self, records):
        with (
            patch(f"{COMMAND}.create_session", return_value=MagicMock()),
            patch(f"{COMMAND}.fetch_sis_courses", return_value=records),
        ):
            call_command("fetch_enrollment", "--semester", self.section.semester.number)

    def test_update_enrollment_from_sis_page(self):
        """A matching SIS record updates the section row in the database."""
        self._run(
            [
                {
                    "class_nbr": self.section.sis_section_number,
                    "enrollment_total": 15,
                    "class_capacity": 25,
                    "wait_tot": 3,
                    "wait_cap": 8,
                }
            ]
        )

        self.section.refresh_from_db()
        self.assertEqual(self.section.enrollment_taken, 15)
        self.assertEqual(self.section.enrollment_limit, 25)
        self.assertEqual(self.section.waitlist_taken, 3)
        self.assertEqual(self.section.waitlist_limit, 8)

    def test_missing_values_default_to_zero(self):
        """Absent enrollment keys fall back to zero rather than crashing."""
        self._run([{"class_nbr": self.section.sis_section_number}])

        self.section.refresh_from_db()
        self.assertEqual(self.section.enrollment_taken, 0)
        self.assertEqual(self.section.enrollment_limit, 0)
        self.assertEqual(self.section.waitlist_taken, 0)
        self.assertEqual(self.section.waitlist_limit, 0)

    def test_unmatched_sections_are_left_untouched(self):
        """Sections with no SIS record keep their existing values."""
        self._run(
            [
                {
                    "class_nbr": 999999,
                    "enrollment_total": 1,
                    "class_capacity": 2,
                    "wait_tot": 0,
                    "wait_cap": 0,
                }
            ]
        )

        self.section.refresh_from_db()
        self.assertEqual(self.section.enrollment_taken, 10)
        self.assertEqual(self.section.enrollment_limit, 20)
        self.assertEqual(self.section.waitlist_taken, 5)
        self.assertEqual(self.section.waitlist_limit, 10)

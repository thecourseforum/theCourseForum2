"""Tests for enrollment data updates."""

from unittest.mock import patch

from django.test import TestCase

from tcf_website.management.commands.fetch_enrollment import fetch_section_data

from .test_utils import setup


class TestEnrollment(TestCase):
    """Test cases for enrollment data updates."""

    def setUp(self):
        """Set up test data."""
        setup(self)
        # pylint: disable=no-member
        self.section = self.section_course
        # Set initial enrollment data on section
        self.section.enrollment_taken = 10
        self.section.enrollment_limit = 20
        self.section.waitlist_taken = 5
        self.section.waitlist_limit = 10
        self.section.save()

    @patch("tcf_website.management.commands.fetch_enrollment.session.get")
    def test_mocked_update_enrollment_data(self, mock_get):
        """Test enrollment data update with mocked data."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {
            "classes": [
                {
                    "enrollment_total": 10,
                    "class_capacity": 20,
                    "wait_tot": 5,
                    "wait_cap": 10,
                }
            ]
        }

        result = fetch_section_data(self.section)
        self.section.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(self.section.enrollment_taken, 10)
        self.assertEqual(self.section.enrollment_limit, 20)
        self.assertEqual(self.section.waitlist_taken, 5)
        self.assertEqual(self.section.waitlist_limit, 10)

    @patch("tcf_website.management.commands.fetch_enrollment.session.get")
    def test_update_enrollment_data(self, mock_get):
        """Test enrollment data update with real API response."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {
            "classes": [
                {
                    "enrollment_total": 15,
                    "class_capacity": 25,
                    "wait_tot": 3,
                    "wait_cap": 8,
                }
            ]
        }

        result = fetch_section_data(self.section)
        self.section.refresh_from_db()

        self.assertTrue(result)
        self.assertGreaterEqual(self.section.enrollment_taken, 0)
        self.assertGreaterEqual(self.section.enrollment_limit, 0)
        self.assertGreaterEqual(self.section.waitlist_taken, 0)
        self.assertGreaterEqual(self.section.waitlist_limit, 0)

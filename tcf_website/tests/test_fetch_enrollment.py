"""Tests for fetch_enrollment management command."""

from unittest.mock import patch

from django.test import TestCase

from tcf_website.management.commands.fetch_enrollment import fetch_section_data

from .test_utils import setup


class FetchEnrollmentTestCase(TestCase):
    """Tests for the fetch_enrollment command."""

    def setUp(self):
        """Set up test data."""
        setup(self)
        # pylint: disable=no-member
        self.section = self.section_course

    @patch("tcf_website.management.commands.fetch_enrollment.session.get")
    def test_fetch_enrollment_success(self, mock_get):
        """Test successful enrollment fetch."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {
            "classes": [
                {
                    "enrollment_total": 15,
                    "class_capacity": 20,
                    "wait_tot": 5,
                    "wait_cap": 10,
                }
            ]
        }

        result = fetch_section_data(self.section)
        self.section.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(self.section.enrollment_taken, 15)
        self.assertEqual(self.section.enrollment_limit, 20)
        self.assertEqual(self.section.waitlist_taken, 5)
        self.assertEqual(self.section.waitlist_limit, 10)

    @patch("tcf_website.management.commands.fetch_enrollment.session.get")
    def test_fetch_enrollment_update_existing(self, mock_get):
        """Test updating existing enrollment data."""
        # Set initial enrollment data on section
        self.section.enrollment_taken = 10
        self.section.enrollment_limit = 20
        self.section.waitlist_taken = 2
        self.section.waitlist_limit = 5
        self.section.save()

        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {
            "classes": [
                {
                    "enrollment_total": 15,
                    "class_capacity": 25,
                    "wait_tot": 8,
                    "wait_cap": 12,
                }
            ]
        }

        result = fetch_section_data(self.section)
        self.section.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(self.section.enrollment_taken, 15)
        self.assertEqual(self.section.enrollment_limit, 25)
        self.assertEqual(self.section.waitlist_taken, 8)
        self.assertEqual(self.section.waitlist_limit, 12)

    @patch("tcf_website.management.commands.fetch_enrollment.session.get")
    def test_fetch_enrollment_empty_response(self, mock_get):
        """Test handling of empty API response."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {"classes": []}

        result = fetch_section_data(self.section)
        self.section.refresh_from_db()

        self.assertFalse(result)
        self.assertIsNone(self.section.enrollment_taken)
        self.assertIsNone(self.section.enrollment_limit)

    @patch("tcf_website.management.commands.fetch_enrollment.session.get")
    def test_fetch_enrollment_api_error(self, mock_get):
        """Test handling of API error."""
        mock_get.return_value.status_code = 500
        mock_get.return_value.raise_for_status.side_effect = Exception("API Error")

        # Set initial values to verify they don't change on error
        self.section.enrollment_taken = 10
        self.section.save()

        result = fetch_section_data(self.section)
        self.section.refresh_from_db()

        self.assertFalse(result)
        # Enrollment data should remain unchanged on error
        self.assertEqual(self.section.enrollment_taken, 10)

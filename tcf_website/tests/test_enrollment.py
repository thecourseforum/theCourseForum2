"""Tests for enrollment data updates."""

from unittest.mock import MagicMock

from django.test import TestCase

from tcf_website.management.commands.fetch_enrollment import fetch_one

from .test_utils import setup


def _mock_json_response(payload):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = lambda: None
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.json.return_value = payload
    return mock_resp


class TestEnrollment(TestCase):
    """Test cases for enrollment data updates."""

    def setUp(self):
        """Set up test data."""
        setup(self)
        self.section = self.section_course
        # Set initial enrollment data on section
        self.section.enrollment_taken = 10
        self.section.enrollment_limit = 20
        self.section.waitlist_taken = 5
        self.section.waitlist_limit = 10
        self.section.save()

    def test_mocked_update_enrollment_data(self):
        """Test enrollment fields parsed from mocked API response."""
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_json_response(
            {
                "classes": [
                    {
                        "enrollment_total": 10,
                        "class_capacity": 20,
                        "wait_tot": 5,
                        "wait_cap": 10,
                    }
                ]
            }
        )

        result = fetch_one(mock_session, self.section.semester.number, self.section)

        self.assertIs(result, self.section)
        self.assertEqual(self.section.enrollment_taken, 10)
        self.assertEqual(self.section.enrollment_limit, 20)
        self.assertEqual(self.section.waitlist_taken, 5)
        self.assertEqual(self.section.waitlist_limit, 10)

    def test_update_enrollment_data(self):
        """Test enrollment fields from a second mocked payload shape."""
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_json_response(
            {
                "classes": [
                    {
                        "enrollment_total": 15,
                        "class_capacity": 25,
                        "wait_tot": 3,
                        "wait_cap": 8,
                    }
                ]
            }
        )

        result = fetch_one(mock_session, self.section.semester.number, self.section)

        self.assertIs(result, self.section)
        self.assertEqual(self.section.enrollment_taken, 15)
        self.assertEqual(self.section.enrollment_limit, 25)
        self.assertEqual(self.section.waitlist_taken, 3)
        self.assertEqual(self.section.waitlist_limit, 8)

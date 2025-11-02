"""Tests for fetch_enrollment management command."""

import gc
import threading
from unittest.mock import patch

from django.db import connections
from django.test import TestCase

from tcf_website.management.commands.fetch_enrollment import fetch_section_data, get_session
from tcf_website.models import SectionEnrollment

from .test_utils import setup


class FetchEnrollmentTestCase(TestCase):
    """Tests for the fetch_enrollment command."""

    def setUp(self):
        """Set up test data."""
        setup(self)
        # pylint: disable=no-member
        self.section = self.section_course

    @patch("tcf_website.management.commands.fetch_enrollment.get_session")
    def test_fetch_enrollment_success(self, mock_get_session):
        """Test successful enrollment fetch."""
        mock_session = mock_get_session.return_value
        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.raise_for_status.return_value = None
        mock_session.get.return_value.json.return_value = {
            "classes": [
                {
                    "enrollment_total": 15,
                    "class_capacity": 20,
                    "wait_tot": 5,
                    "wait_cap": 10,
                }
            ]
        }

        fetch_section_data(self.section)

        enrollment = SectionEnrollment.objects.get(section=self.section)
        self.assertEqual(enrollment.enrollment_taken, 15)
        self.assertEqual(enrollment.enrollment_limit, 20)
        self.assertEqual(enrollment.waitlist_taken, 5)
        self.assertEqual(enrollment.waitlist_limit, 10)

    @patch("tcf_website.management.commands.fetch_enrollment.get_session")
    def test_fetch_enrollment_update_existing(self, mock_get_session):
        """Test updating existing enrollment data."""
        # Create initial enrollment
        SectionEnrollment.objects.create(
            section=self.section,
            enrollment_taken=10,
            enrollment_limit=20,
            waitlist_taken=2,
            waitlist_limit=5,
        )

        mock_session = mock_get_session.return_value
        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.raise_for_status.return_value = None
        mock_session.get.return_value.json.return_value = {
            "classes": [
                {
                    "enrollment_total": 15,
                    "class_capacity": 25,
                    "wait_tot": 8,
                    "wait_cap": 12,
                }
            ]
        }

        fetch_section_data(self.section)

        enrollment = SectionEnrollment.objects.get(section=self.section)
        self.assertEqual(enrollment.enrollment_taken, 15)
        self.assertEqual(enrollment.enrollment_limit, 25)
        self.assertEqual(enrollment.waitlist_taken, 8)
        self.assertEqual(enrollment.waitlist_limit, 12)

    @patch("tcf_website.management.commands.fetch_enrollment.get_session")
    def test_fetch_enrollment_empty_response(self, mock_get_session):
        """Test handling of empty API response."""
        mock_session = mock_get_session.return_value
        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.raise_for_status.return_value = None
        mock_session.get.return_value.json.return_value = {"classes": []}

        result = fetch_section_data(self.section)

        self.assertFalse(result)
        self.assertEqual(SectionEnrollment.objects.count(), 0)

    @patch("tcf_website.management.commands.fetch_enrollment.get_session")
    def test_fetch_enrollment_api_error(self, mock_get_session):
        """Test handling of API error."""
        mock_session = mock_get_session.return_value
        mock_session.get.return_value.status_code = 500
        mock_session.get.return_value.raise_for_status.side_effect = Exception("API Error")

        result = fetch_section_data(self.section)

        self.assertFalse(result)
        self.assertEqual(SectionEnrollment.objects.count(), 0)

    @patch("tcf_website.management.commands.fetch_enrollment.get_session")
    def test_no_resource_leaks(self, mock_get_session):
        """Test that threads and database connections are properly cleaned up."""
        mock_session = mock_get_session.return_value
        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.raise_for_status.return_value = None
        mock_session.get.return_value.json.return_value = {
            "classes": [{"enrollment_total": 15, "class_capacity": 20, "wait_tot": 0, "wait_cap": 0}]
        }

        # Check thread isolation: each thread gets its own session
        sessions = []
        for _ in range(5):
            thread = threading.Thread(target=lambda: sessions.append(get_session()))
            thread.start()
            thread.join()
        self.assertEqual(len(set(id(s) for s in sessions)), 5, "Each thread should have its own session")

        # Check connection cleanup: no connection leak after fetch
        initial_connections = len([c for c in connections.all() if c.is_usable()])
        fetch_section_data(self.section)
        gc.collect()
        final_connections = len([c for c in connections.all() if c.is_usable()])
        self.assertLessEqual(final_connections, initial_connections + 1, "Connections should be closed")

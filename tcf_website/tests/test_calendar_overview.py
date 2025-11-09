"""Tests for calendar overview functionality."""

from django.test import TestCase, Client


class CalendarOverviewTests(TestCase):
    """Tests for calendar overview functionality."""

    def setUp(self):
        self.client = Client()

    def test_calendar_route_ok(self):
        """Test that the calendar route is reachable."""
        resp = self.client.get("/clubs/calendar/")
        self.assertIn(resp.status_code, (200, 302))



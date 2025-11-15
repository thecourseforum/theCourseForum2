"""Tests for calendar overview functionality."""

from unittest.mock import patch

from django.test import TestCase, Client


class CalendarOverviewTests(TestCase):
    """Tests for calendar overview functionality."""

    def setUp(self):
        """
        Prepare the test case by creating a Django test client.
        
        Attaches a django.test.Client instance to `self.client` for use in test methods; run before each test.
        """
        self.client = Client()

    def test_calendar_route_ok(self):
        """Test that the calendar route is reachable."""
        resp = self.client.get("/clubs/calendar/")
        self.assertIn(resp.status_code, (200, 302))

    @patch('tcf_website.views.calendar.presence.get_events')
    def test_events_sorted_by_date(self, mock_get_events):
        """Test that events are sorted ascending by start date."""
        # Mock events out of order
        mock_events = [
            {
                "eventName": "Event C",
                "organizationName": "Org C",
                "uri": "c",
                "startDateTimeUtc": "2026-01-03T10:00:00Z",
            },
            {
                "eventName": "Event A",
                "organizationName": "Org A",
                "uri": "a",
                "startDateTimeUtc": "2026-01-01T10:00:00Z",
            },
            {
                "eventName": "Event B",
                "organizationName": "Org B",
                "uri": "b",
                "startDateTimeUtc": "2026-01-02T10:00:00Z",
            },
        ]
        mock_get_events.return_value = mock_events

        resp = self.client.get("/clubs/calendar/")
        self.assertEqual(resp.status_code, 200)

        # Check context has sorted groups
        upcoming_groups = resp.context['upcoming_groups']
        dates = list(upcoming_groups.keys())
        self.assertEqual(dates, ['2026-01-01', '2026-01-02', '2026-01-03'])
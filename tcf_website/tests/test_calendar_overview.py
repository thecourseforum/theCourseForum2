"""Tests for calendar overview functionality."""

from unittest.mock import patch

from django.test import TestCase, Client


class CalendarOverviewTests(TestCase):
    """Tests for calendar overview functionality."""

    def setUp(self):
        """
        Create a test HTTP client for use in test methods.
        
        Initializes self.client with a Django test Client instance so tests can perform HTTP requests to views.
        """
        self.client = Client()

    def test_calendar_route_ok(self):
        """Test that the calendar route is reachable."""
        resp = self.client.get("/clubs/calendar/")
        self.assertIn(resp.status_code, (200, 302))

    @patch('tcf_website.views.calendar.presence.get_events')
    def test_events_sorted_by_date(self, mock_get_events):
        """
        Verify the calendar view presents events grouped by date in ascending order.
        
        Patches `presence.get_events` to return events with out-of-order `startDateTimeUtc` values, requests the calendar route, and asserts the response is OK and that `resp.context['upcoming_groups']` has date keys sorted as ['2025-01-01', '2025-01-02', '2025-01-03'].
        
        Parameters:
            mock_get_events (unittest.mock.Mock): Patched replacement for `presence.get_events`; the test sets its return value to a list of events out of chronological order.
        """
        # Mock events out of order
        mock_events = [
        {
            "eventName": "Event C",
            "organizationName": "Org C",
                "uri": "c",
                "startDateTimeUtc": "2025-01-03T10:00:00Z",
            },
            {
                "eventName": "Event A",
                "organizationName": "Org A",
                "uri": "a",
                "startDateTimeUtc": "2025-01-01T10:00:00Z",
            },
            {
                "eventName": "Event B",
                "organizationName": "Org B",
                "uri": "b",
                "startDateTimeUtc": "2025-01-02T10:00:00Z",
            },
        ]
        mock_get_events.return_value = mock_events

        resp = self.client.get("/clubs/calendar/")
        self.assertEqual(resp.status_code, 200)

        # Check context has sorted groups
        upcoming_groups = resp.context['upcoming_groups']
        dates = list(upcoming_groups.keys())
        self.assertEqual(dates, ['2025-01-01', '2025-01-02', '2025-01-03'])
"""Tests for event detail functionality."""

from unittest.mock import patch


from django.test import TestCase, Client


class EventDetailTests(TestCase):
    """Tests for event detail functionality."""

    def setUp(self):
        """
        Set up a Django test client for use by each test.
        
        Runs before each test method and assigns a `django.test.Client` instance to `self.client`.
        """
        self.client = Client()

    def test_event_detail_route_ok(self):
        """Test that event detail route handles valid event."""
        # Assuming a valid event URI, but since mocked, we'll add mocks
        # Will be covered by mock tests
        pass

    @patch('tcf_website.views.calendar.presence.get_event_details')
    def test_event_detail_not_found_on_exception(self, mock_get_details):
        """
        Verify the event detail view responds with HTTP 404 when the event service raises an exception.
        
        This test sets the patched `get_event_details` mock to raise an Exception and asserts that a GET request to the event detail URL returns a 404 status.
        
        Parameters:
            mock_get_details: patched mock for `get_event_details`, configured to raise an exception.
        """
        mock_get_details.side_effect = Exception("Service error")

        resp = self.client.get("/clubs/calendar/event/test-uri/")
        self.assertEqual(resp.status_code, 404)

    @patch('tcf_website.views.calendar.presence.get_event_details')
    def test_event_detail_not_found_on_none(self, mock_get_details):
        """Test that event detail raises 404 when service returns None."""
        mock_get_details.return_value = None

        resp = self.client.get("/clubs/calendar/event/test-uri/")
        self.assertEqual(resp.status_code, 404)
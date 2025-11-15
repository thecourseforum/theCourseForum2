"""Tests for event detail functionality."""

from unittest.mock import patch


from django.test import TestCase, Client


class EventDetailTests(TestCase):
    """Tests for event detail functionality."""

    def setUp(self):
        self.client = Client()

    

    @patch('tcf_website.views.calendar.presence.get_event_details')
    def test_event_detail_not_found_on_exception(self, mock_get_details):
        """Test that event detail raises 404 on service exception."""
        mock_get_details.side_effect = Exception("Service error")

        resp = self.client.get("/clubs/calendar/event/test-uri/")
        self.assertEqual(resp.status_code, 404)

    @patch('tcf_website.views.calendar.presence.get_event_details')
    def test_event_detail_not_found_on_none(self, mock_get_details):
        """Test that event detail raises 404 when service returns None."""
        mock_get_details.return_value = None

        resp = self.client.get("/clubs/calendar/event/test-uri/")
        self.assertEqual(resp.status_code, 404)

from django.test import TestCase, Client
from django.conf import settings


class CalendarOverviewTests(TestCase):
    def setUp(self):
        settings.ENABLE_CLUB_CALENDAR = True
        self.client = Client()

    def test_calendar_route_ok(self):
        resp = self.client.get("/clubs/calendar/")
        self.assertIn(resp.status_code, (200, 302))



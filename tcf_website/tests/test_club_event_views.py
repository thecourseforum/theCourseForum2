"""Public event-list pages and progressive-enhancement contracts."""

from django.test import TestCase
from django.urls import reverse

from tcf_website.models import Club, ClubCategory, ClubEvent
from tcf_website.tests.test_club_events import local_time


class ClubEventViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ClubCategory.objects.create(name="Academic", slug="ACAD")
        cls.club = Club.objects.create(name="Hoo Hacks", category=cls.category)
        cls.event = ClubEvent.objects.create(
            title="Hack night",
            category=cls.category,
            starts_at=local_time(6, 18),
            ends_at=local_time(6, 20),
            location="Rice Hall",
            is_sample=True,
        )
        cls.event.hosts.add(cls.club)

    def list_url(self):
        return reverse("club_events")

    def get_list(self, **params):
        return self.client.get(
            self.list_url(),
            {
                "mode": "clubs",
                "from": "2026-11-01",
                "to": "2026-11-30",
                **params,
            },
        )

    def test_public_list_reuses_shell_and_discloses_samples(self):
        response = self.get_list()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "site/common/base.html")
        self.assertContains(response, "Hack night")
        self.assertContains(response, "Friday, November 6")
        self.assertContains(response, "6:00 PM")
        self.assertContains(response, "Sample event")
        self.assertContains(response, "All times are Eastern")
        self.assertContains(response, "Coming soon")
        self.assertContains(response, "data-event-detail")

    def test_canonical_club_mode_preserves_filter_values(self):
        response = self.client.get(
            self.list_url(), {"q": "Hoo & Hacks", "interest": ["Tech", "Arts"]}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("mode=clubs", response.url)
        self.assertIn("q=Hoo+%26+Hacks", response.url)
        self.assertIn("interest=Tech&interest=Arts", response.url)

    def test_course_mode_toggle_leaves_events_page(self):
        response = self.get_list()
        self.assertContains(response, 'href="/browse/"')

    def test_partial_contains_results_without_duplicate_shell(self):
        response = self.client.get(
            self.list_url(),
            {
                "mode": "clubs",
                "from": "2026-11-01",
                "to": "2026-11-30",
                "partial": "results",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertContains(response, "Hack night")
        self.assertNotContains(response, "<!DOCTYPE")

    def test_invalid_dates_show_errors_and_preserve_input(self):
        response = self.get_list(
            **{"from": "2026-11-30", "to": "2026-11-01", "q": "Rice"}
        )
        self.assertContains(response, "Choose an end date")
        self.assertContains(response, 'value="Rice"')
        self.assertContains(response, 'value="2026-11-30"')
        self.assertNotContains(response, "Hack night")

    def test_empty_results_offer_reset(self):
        response = self.get_list(q="No matching event")
        self.assertContains(response, "No events match your filters")
        self.assertContains(response, "Reset filters")

    def test_pagination_retains_filters_and_has_stable_occurrences(self):
        """Verify page two retains filters and excludes first-page occurrences."""
        for i in range(16):
            event = ClubEvent.objects.create(
                title=f"Extra {i}",
                category=self.category,
                starts_at=local_time(7, 18),
                ends_at=local_time(7, 20),
            )
            event.hosts.add(self.club)
        response = self.get_list(club=self.club.pk, page=2)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(len(response.context["page_obj"]), 2)
        self.assertContains(response, f"club={self.club.pk}")
        self.assertContains(response, "from=2026-11-01")
        self.assertNotContains(response, "Hack night")

    def test_details_have_normal_page_and_modal_fragment(self):
        url = reverse("club_event_detail", args=[self.event.pk])
        page = self.client.get(url, {"mode": "clubs"})
        self.assertContains(page, "Hack night")
        self.assertContains(page, "Rice Hall")
        self.assertTemplateUsed(page, "site/common/base.html")
        modal = self.client.get(
            url,
            {"mode": "clubs", "partial": "details"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertContains(modal, 'id="clubEventTitle"')
        self.assertContains(modal, "Sample event")
        self.assertNotContains(modal, "<!DOCTYPE")

    def test_private_and_hostless_events_are_not_accessible(self):
        url = reverse("club_event_detail", args=[self.event.pk])
        self.event.is_public = False
        self.event.save()
        self.assertEqual(self.client.get(url, {"mode": "clubs"}).status_code, 404)
        self.event.is_public = True
        self.event.save()
        self.event.hosts.clear()
        self.assertEqual(self.client.get(url, {"mode": "clubs"}).status_code, 404)

    def test_online_location_is_not_repeated_in_details(self):
        self.event.location = "Online"
        self.event.online = True
        self.event.save()
        response = self.client.get(
            reverse("club_event_detail", args=[self.event.pk]), {"mode": "clubs"}
        )
        self.assertContains(response, "<dd>Online</dd>", html=True)

    def test_untrusted_event_text_is_escaped(self):
        self.event.title = '<script>alert("xss")</script>'
        self.event.save()
        response = self.get_list()
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, self.event.title)

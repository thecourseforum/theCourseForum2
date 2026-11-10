"""Event-list contracts: dates, visibility, filtering, and co-host deduplication."""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.test import TestCase

from tcf_website.clubs.events import ClubEventFilterForm, filtered_events
from tcf_website.models import Club, ClubCategory, ClubEvent

EASTERN = ZoneInfo("America/New_York")


def local_time(day, hour=0, month=11):
    return datetime(2026, month, day, hour, tzinfo=EASTERN)


class ClubEventQueryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ClubCategory.objects.create(name="Technology", slug="TECH")
        cls.other_category = ClubCategory.objects.create(name="Arts", slug="ARTS")
        cls.club = Club.objects.create(name="Hoo Hacks", category=cls.category)
        cls.cohost = Club.objects.create(name="Women in CS", category=cls.category)
        cls.event = cls.create_event("Kickoff", hosts=[cls.club, cls.cohost])
        cls.cancelled = cls.create_event("Cancelled dinner", is_cancelled=True)
        cls.private = cls.create_event("Private meeting", is_public=False)

    @classmethod
    def create_event(cls, title, hosts=None, **kwargs):
        """Create an occurrence with overridable defaults and optional co-hosts."""
        fields = {
            "title": title,
            "description": "Learn to build things together.",
            "category": cls.category,
            "starts_at": local_time(6, 18),
            "ends_at": local_time(6, 20),
            "location": "Rice Hall",
            "interests": ["Tech", "Entrepreneurship"],
        }
        fields.update(kwargs)
        event = ClubEvent.objects.create(**fields)
        event.hosts.set(hosts or [cls.club])
        return event

    def results(self, **params):
        form = ClubEventFilterForm({"from": "2026-11-01", "to": "2026-11-30", **params})
        self.assertTrue(form.is_valid(), form.errors)
        return list(filtered_events(form))

    def test_default_visibility_and_cohost_deduplication(self):
        self.assertEqual(self.results(), [self.event])

    def test_cancelled_is_opt_in_but_private_is_always_hidden(self):
        self.assertCountEqual(
            self.results(show_cancelled="on"), [self.event, self.cancelled]
        )

    def test_keyword_matches_title_description_host_and_location(self):
        """Verify keyword searches match each supported event or host text field."""
        for keyword in ["kickoff", "build", "Women in CS", "rice"]:
            with self.subTest(keyword=keyword):
                self.assertEqual(self.results(q=keyword), [self.event])

    def test_filters_combine_and_query_deduplicates_hosts(self):
        self.assertEqual(
            self.results(
                q="Hoo", category=self.category.pk, club=self.cohost.pk, interest="Tech"
            ),
            [self.event],
        )
        self.assertEqual(self.results(category=self.other_category.pk), [])
        self.assertEqual(self.results(q="unmatched"), [])

    def test_interest_matching_is_exact(self):
        self.create_event(
            "Art workshop",
            interests=["Arts"],
            starts_at=local_time(7, 18),
            ends_at=local_time(7, 20),
        )
        self.assertEqual(self.results(interest="Tech"), [self.event])

    def test_inclusive_date_range_uses_overlap_not_start_date(self):
        overnight = self.create_event(
            "Overnight", starts_at=local_time(5, 23), ends_at=local_time(6, 2)
        )
        self.create_event(
            "Ends at boundary", starts_at=local_time(5, 20), ends_at=local_time(6)
        )
        self.create_event(
            "Starts next day", starts_at=local_time(7), ends_at=local_time(7, 2)
        )
        self.assertCountEqual(
            self.results(**{"from": "2026-11-06", "to": "2026-11-06"}),
            [overnight, self.event],
        )

    def test_all_day_exclusive_end_and_display_end(self):
        event = self.create_event(
            "Registration", all_day=True, starts_at=local_time(6), ends_at=local_time(9)
        )
        self.assertIn(event, self.results(**{"from": "2026-11-08", "to": "2026-11-08"}))
        self.assertNotIn(
            event, self.results(**{"from": "2026-11-09", "to": "2026-11-09"})
        )
        self.assertEqual(event.display_end.date(), local_time(8).date())

    def test_eastern_day_spanning_dst_fallback_is_25_hours(self):
        event = self.create_event(
            "Late on DST day", starts_at=local_time(1, 23), ends_at=local_time(2)
        )
        self.assertEqual(
            self.results(**{"from": "2026-11-01", "to": "2026-11-01"}), [event]
        )

    def test_stable_order_and_latest_sort(self):
        later = self.create_event(
            "Later", starts_at=local_time(7, 18), ends_at=local_time(7, 20)
        )
        self.assertEqual(self.results(), [self.event, later])
        self.assertEqual(self.results(sort="latest"), [later, self.event])

    def test_invalid_filters_never_silently_return_all_events(self):
        """Verify malformed or unknown filters produce errors and no results."""
        for params in [
            {"from": "bad"},
            {"from": "2026-11-30", "to": "2026-11-01"},
            {"club": "invalid"},
            {"category": "999999"},
            {"interest": "unrecognized"},
            {"sort": "unsafe"},
            {"to": "9999-12-31"},
        ]:
            with self.subTest(params=params):
                form = ClubEventFilterForm(params)
                self.assertFalse(form.is_valid())
                self.assertFalse(filtered_events(form).exists())

    def test_end_must_be_after_start(self):
        self.event.ends_at = self.event.starts_at
        with self.assertRaises(ValidationError):
            self.event.full_clean()

    def test_all_day_boundaries_must_be_eastern_midnight(self):
        self.event.all_day = True
        with self.assertRaises(ValidationError):
            self.event.full_clean()

    def test_source_link_rejects_unsafe_schemes_and_sample_links(self):
        """Verify unsafe and sample links are hidden while valid source links work."""
        for url in ["javascript:alert(1)", "//example.com/event", "https://[bad"]:
            self.event.source_url = url
            self.assertEqual(self.event.public_source_url, "")
        self.event.source_url = "https://hoosinvolved.virginia.edu/event/123"
        self.assertEqual(self.event.public_source_url, self.event.source_url)
        self.event.is_sample = True
        self.assertEqual(self.event.public_source_url, "")

    def test_interest_data_must_be_a_list_of_nonempty_strings(self):
        """Reject non-list interests, empty names, and non-string entries."""
        for value in [{"Tech": True}, [""], [1]]:
            self.event.interests = value
            with self.assertRaises(ValidationError):
                self.event.full_clean()

"""Repeatable, local-only sample loading must preserve real club data."""

from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from tcf_website.models import Club, ClubCategory, ClubEvent
from tcf_website.tests.test_club_events import local_time


class SampleClubEventTests(TestCase):
    def load_samples(self):
        call_command("load_sample_club_events", stdout=StringIO())

    def test_loads_design_samples_and_is_repeatable(self):
        self.load_samples()
        ids = list(ClubEvent.objects.values_list("pk", flat=True))
        self.assertEqual(ClubEvent.objects.count(), 21)
        self.assertEqual(Club.objects.count(), 18)
        self.assertEqual(ClubEvent.objects.filter(is_sample=True).count(), 21)
        self.load_samples()
        self.assertEqual(list(ClubEvent.objects.values_list("pk", flat=True)), ids)
        self.assertEqual(Club.objects.count(), 18)

    def test_seed_keeps_cohosts_cancelled_and_overnight_records(self):
        """Verify sample loading retains co-hosts, cancellations, and overnight spans."""
        self.load_samples()
        self.assertTrue(ClubEvent.objects.filter(is_cancelled=True).exists())
        self.assertEqual(
            ClubEvent.objects.get(source_key="sample:veo-pitch-night").hosts.count(), 2
        )
        self.assertTrue(
            any(
                event.local_start.date() != event.display_end.date()
                for event in ClubEvent.objects.filter(all_day=False)
            )
        )

    def test_all_day_source_inclusive_end_becomes_exclusive_boundary(self):
        self.load_samples()
        event = ClubEvent.objects.get(source_key="sample:hoo-hacks-registration")
        self.assertEqual(event.starts_at, local_time(6))
        self.assertEqual(event.ends_at, local_time(9))
        event.full_clean()

    def test_does_not_modify_existing_club_profile_or_unrelated_events(self):
        category = ClubCategory.objects.create(name="Existing", slug="EXIS")
        club = Club.objects.create(
            name="Hoo Hacks",
            category=category,
            description="Verified description",
            meeting_time="Verified time",
        )
        event = ClubEvent.objects.create(
            title="Real event",
            category=category,
            starts_at=local_time(1, 18),
            ends_at=local_time(1, 20),
        )
        self.load_samples()
        club.refresh_from_db()
        event.refresh_from_db()
        self.assertEqual(club.description, "Verified description")
        self.assertEqual(club.category, category)
        self.assertEqual(club.meeting_time, "Verified time")
        self.assertEqual(event.title, "Real event")
        self.assertFalse(event.is_sample)

    @override_settings(ENVIRONMENT="prod")
    def test_refuses_production(self):
        with self.assertRaisesMessage(CommandError, "local development"):
            self.load_samples()
        self.assertEqual(Club.objects.count(), 0)

    def test_non_sample_source_collision_rolls_back(self):
        category = ClubCategory.objects.create(name="Existing", slug="EXIS")
        event = ClubEvent.objects.create(
            source_key="sample:tcf-open-house",
            title="Protected event",
            category=category,
            starts_at=local_time(1, 18),
            ends_at=local_time(1, 20),
        )
        with self.assertRaises(CommandError):
            self.load_samples()
        event.refresh_from_db()
        self.assertEqual(event.title, "Protected event")
        self.assertFalse(event.is_sample)
        self.assertEqual(Club.objects.count(), 0)

"""Load the approved November 2026 design examples, without fetching real data."""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tcf_website.management.commands.load_clubs import Command as ClubLoader
from tcf_website.models import Club, ClubEvent
from tcf_website.models.club_event import EVENT_TIME_ZONE


class Command(BaseCommand):
    help = "Load repeatable November 2026 sample club events for local development."

    @transaction.atomic
    def handle(self, *args, **options):
        if settings.ENVIRONMENT not in ("local", "ci"):
            raise CommandError(
                "Sample events are for local development and tests only."
            )
        path = Path(__file__).parent / "club_data" / "sample_events.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        loader = ClubLoader(stdout=self.stdout)
        category_cache = {}
        categories = {
            item["slug"]: loader.get_or_create_category(item["name"], category_cache)
            for item in data["categories"]
        }
        clubs = {}
        for item in data["clubs"]:
            # Existing Club names are not unique. Reuse the oldest match without
            # overwriting real descriptions, categories, or admin corrections.
            club = Club.objects.filter(name=item["name"]).order_by("pk").first()
            if club is None:
                club = Club.objects.create(
                    name=item["name"],
                    category=categories[item["category"]],
                    description=f"Sample club profile. {item['description']}",
                    application_required=bool(item["applicationRequired"]),
                    meeting_time=item["meetingTime"],
                )
            clubs[item["slug"]] = club

        for item in data["events"]:
            key = f"sample:{item['id']}"
            existing = (
                ClubEvent.objects.select_for_update().filter(source_key=key).first()
            )
            if existing and not existing.is_sample:
                raise CommandError(f"Refusing to replace non-sample event {key}.")
            all_day = item.get("allDay", False)
            if all_day:
                start = datetime.combine(
                    date.fromisoformat(item["startDate"]), time.min, EVENT_TIME_ZONE
                )
                # The design's dates are inclusive; storage uses an exclusive end.
                end = datetime.combine(
                    date.fromisoformat(item["endDate"]) + timedelta(days=1),
                    time.min,
                    EVENT_TIME_ZONE,
                )
            else:
                start = datetime.fromisoformat(item["start"])
                end = datetime.fromisoformat(item["end"])
            event = existing or ClubEvent(source_key=key)
            for field, value in {
                "title": item["title"],
                "description": item["description"],
                "category": categories[item["category"]],
                "interests": item["interests"],
                "starts_at": start,
                "ends_at": end,
                "all_day": all_day,
                "location": item["location"],
                "online": item.get("online", False),
                "is_cancelled": item.get("cancelled", False),
                "is_sample": True,
                "is_public": True,
                "source_url": "",
            }.items():
                setattr(event, field, value)
            event.full_clean()
            event.save()
            event.hosts.set([clubs[slug] for slug in item["clubSlugs"]])
        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(data['events'])} sample events. Preview: "
                "/club-events/?mode=clubs&from=2026-11-01&to=2026-11-30"
            )
        )

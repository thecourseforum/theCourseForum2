"""Shared event occurrences. Ingestion and calendar export live outside this model."""

import uuid
from datetime import time, timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

EVENT_TIME_ZONE = ZoneInfo("America/New_York")


class ClubEvent(models.Model):
    """One occurrence, potentially hosted by several clubs; end is exclusive."""

    source_key = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    hosts = models.ManyToManyField("Club", related_name="events")
    category = models.ForeignKey("ClubCategory", on_delete=models.PROTECT)
    interests = models.JSONField(default=list, blank=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True)
    online = models.BooleanField(default=False)
    source_url = models.URLField(max_length=500, blank=True)
    is_public = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)
    is_sample = models.BooleanField(default=False)

    class Meta:
        ordering = ["starts_at", "pk"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(ends_at__gt=models.F("starts_at")),
                name="club_event_positive_duration",
            )
        ]

    def __str__(self):
        return self.title

    @property
    def local_start(self):
        """Always group and display events in UVA's timezone, not server UTC."""
        return timezone.localtime(self.starts_at, EVENT_TIME_ZONE)

    @property
    def display_end(self):
        """Convert an all-day exclusive boundary to the last included date."""
        end = timezone.localtime(self.ends_at, EVENT_TIME_ZONE)
        return end - timedelta(days=1) if self.all_day else end

    @property
    def public_source_url(self):
        """Sample records have no real source page; never render unsafe schemes."""
        parsed = urlsplit(self.source_url)
        if not self.is_sample and parsed.scheme in ("https", "http") and parsed.netloc:
            return self.source_url
        return ""

    def clean(self):
        super().clean()
        if not isinstance(self.interests, list) or any(
            not isinstance(value, str) or not value.strip() for value in self.interests
        ):
            raise ValidationError(
                {"interests": "Use a list of nonempty interest names."}
            )
        if self.starts_at and self.ends_at:
            if timezone.is_naive(self.starts_at) or timezone.is_naive(self.ends_at):
                raise ValidationError("Event times must include a timezone.")
            if self.ends_at <= self.starts_at:
                raise ValidationError({"ends_at": "End must be after start."})
            if self.all_day and any(
                timezone.localtime(value, EVENT_TIME_ZONE).time() != time.min
                for value in (self.starts_at, self.ends_at)
            ):
                raise ValidationError("All-day boundaries must be Eastern midnight.")

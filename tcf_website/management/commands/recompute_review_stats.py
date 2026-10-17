"""Backfill denormalized review statistics from existing reviews (issue #982).

Rebuilds every ``CourseStats`` and ``CourseInstructorStats`` row from scratch off
the current set of non-hidden reviews. Run this once after deploying the stats
models / migration, and any time the stored aggregates might have drifted from the
source reviews (e.g. bulk imports that bypass the model signals).

Usage:
    python manage.py recompute_review_stats
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from tcf_website.models.stats import recompute_all_stats


class Command(BaseCommand):
    """Recompute all stored course / course-instructor review statistics."""

    help = "Backfill CourseStats and CourseInstructorStats from existing reviews."

    def handle(self, *args, **options):
        self.stdout.write("Recomputing review statistics from all reviews...")
        with transaction.atomic():
            summary = recompute_all_stats(verbose_writer=self.stdout.write)
        self.stdout.write(
            self.style.SUCCESS(
                "Done. Wrote {course_instructor_stats} CourseInstructorStats and "
                "{course_stats} CourseStats rows.".format(**summary)
            )
        )

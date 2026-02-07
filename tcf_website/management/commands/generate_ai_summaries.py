"""Manual generator for AI review summaries."""

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Exists, Max, OuterRef

from ...models import Course, Instructor, Review, ReviewLLMSummary
from ...services.review_summary import generate_review_summary


# pylint: disable=too-many-branches,too-many-locals,no-member


class Command(BaseCommand):
    """Command to manually generate AI summaries for course/instructor pairs.

    Usage examples:
    # Help command:
    docker compose exec web python manage.py generate_ai_summaries help

    # Dry run: show top 20 pairs by written-review count (no LLM calls)
    python manage.py generate_ai_summaries --dry-run
    OR
    docker compose exec web python manage.py generate_ai_summaries --dry-run

    # Generate for top 30 course / instructor pairs with at least 3 written reviews
    python manage.py generate_ai_summaries --limit 30 --min-reviews 3
    OR
    docker compose exec web python manage.py generate_ai_summaries --limit 30 --min-reviews 3

    # Generate for top 20 course / instructor pairs missing a summary
    python manage.py generate_ai_summaries --limit 20 --missing-only
    OR
    docker compose exec web python manage.py generate_ai_summaries --limit 20 --missing-only

    # Generate for a specific course/instructor pair
    python manage.py generate_ai_summaries --course-id 1 --instructor-id 4019
    docker compose exec web python manage.py generate_ai_summaries
        --course-id 1 --instructor-id 4019
    """

    help = "Generate AI summaries manually for course/instructor pairs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=15,
            help="Number of top course/instructor pairs by review count to summarize.",
        )
        parser.add_argument(
            "--course-id",
            type=int,
            help="Specific course id to summarize (must be used with --instructor-id).",
        )
        parser.add_argument(
            "--instructor-id",
            type=int,
            help="Specific instructor id to summarize (must be used with --course-id).",
        )
        parser.add_argument(
            "--min-reviews",
            type=int,
            default=1,
            help="Minimum number of written reviews required to generate a summary.",
        )
        parser.add_argument(
            "--max-reviews",
            type=int,
            default=25,
            help="Use only the top N most recent written reviews in the prompt (default: 25).",
        )
        parser.add_argument(
            "--missing-only",
            action="store_true",
            help="Only include pairs without an existing summary.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which pairs would be processed without calling the model.",
        )

    def handle(self, *args: Any, **options: Any):  # pylint: disable=unused-argument,too-many-locals
        if not getattr(settings, "OPENROUTER_API_KEY", ""):
            raise CommandError("OPENROUTER_API_KEY is not configured.")

        course_id = options.get("course_id")
        instructor_id = options.get("instructor_id")
        limit = options.get("limit")
        min_reviews = options.get("min_reviews")
        max_reviews = options.get("max_reviews") or 20
        missing_only = options.get("missing_only")
        dry_run = options.get("dry_run")

        if bool(course_id) ^ bool(instructor_id):
            raise CommandError(
                "Provide both --course-id and --instructor-id together, or neither."
            )

        # Base queryset: visible, non-toxic, with text
        base_reviews = Review.objects.filter(
            hidden=False, toxicity_rating__lt=settings.TOXICITY_THRESHOLD
        ).exclude(text="")

        pairs: list[tuple[int, int, int, int]] = []

        if course_id and instructor_id:
            if missing_only and ReviewLLMSummary.objects.filter(
                course_id=course_id, instructor_id=instructor_id, club__isnull=True
            ).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping course {course_id} / instructor {instructor_id}: "
                        "summary already exists."
                    )
                )
                return
            review_count = base_reviews.filter(
                course_id=course_id, instructor_id=instructor_id
            ).count()
            if review_count < min_reviews:
                msg = (
                    f"Skipping course {course_id} / instructor {instructor_id}: "
                    f"only {review_count} reviews."
                )
                self.stdout.write(self.style.WARNING(msg))
                return
            latest_id = (
                base_reviews.filter(course_id=course_id, instructor_id=instructor_id)
                .order_by("-id")
                .values_list("id", flat=True)
                .first()
                or 0
            )
            pairs = [(course_id, instructor_id, review_count, latest_id)]
        else:
            agg = (
                base_reviews.values("course_id", "instructor_id")
                .annotate(review_count=Count("id"), last_id=Max("id"))
                .filter(review_count__gte=min_reviews)
                .order_by("-review_count")
            )
            if missing_only:
                existing_summaries = ReviewLLMSummary.objects.filter(
                    course_id=OuterRef("course_id"),
                    instructor_id=OuterRef("instructor_id"),
                    club__isnull=True,
                )
                agg = agg.annotate(has_summary=Exists(existing_summaries)).filter(
                    has_summary=False
                )
            agg = agg[:limit]
            pairs = [
                (row["course_id"], row["instructor_id"], row["review_count"], row["last_id"])
                for row in agg
            ]

        if not pairs:
            self.stdout.write(self.style.WARNING("No pairs matched criteria."))
            return

        self.stdout.write(f"Processing {len(pairs)} pair(s)...")

        for course_id, instructor_id, review_count, latest_id in pairs:
            course = Course.objects.get(id=course_id)
            instructor = Instructor.objects.get(id=instructor_id)
            qs = base_reviews.filter(course=course, instructor=instructor).order_by(
                "-created"
            )

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would summarize {course.code()} / {instructor.full_name} "
                    f"({review_count} reviews)"
                )
                continue

            summary_text, error, model_used = generate_review_summary(
                course, instructor, qs, max_reviews=max_reviews
            )
            if not summary_text:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed for {course.code()} / {instructor.full_name}: {error}"
                    )
                )
                continue

            ReviewLLMSummary.objects.update_or_create(
                course=course,
                instructor=instructor,
                defaults={
                    "summary_text": summary_text,
                    "source_review_count": review_count,
                    "last_review_id": latest_id,
                    "source_metadata": {},
                    "model_id": model_used or getattr(settings, "OPENROUTER_MODEL", ""),
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Saved summary for {course.code()} / {instructor.full_name} "
                    f"({review_count} reviews) using {model_used or 'unknown model'}"
                )
            )

"""Generate AI review summaries for course-instructor pairs via OpenRouter."""

from datetime import datetime
import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Exists, F, OuterRef

from ...models import Course, Instructor, Review, ReviewLLMSummary, Semester

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_REVIEW_CHARS = 1000
MIN_REVIEW_COUNT = 5  # minimum number of reviews to create summary
MAX_REVIEW_COUNT = 50  # maximum number of reviews to include in the prompt


def _resolve_semester(raw):
    """Return Semester instance, or None if raw is None."""
    if raw is None:
        return None
    parts = raw.split("_")
    if (
        len(parts) != 2
        or not parts[0].isdigit()
        or len(parts[0]) != 4
        or parts[1].upper() not in ["SPRING", "FALL", "JANUARY", "SUMMER"]
    ):
        raise CommandError(
            "--semester must be in format <year>_<season> (e.g. 2024_spring)"
        )
    try:
        year, season = parts
        return Semester.objects.get(year=int(year), season=season.upper())
    except Semester.DoesNotExist as exc:
        raise CommandError(f"Unknown semester: {raw}") from exc


def _build_messages(course, instructor, reviews):
    bullets = []
    for r in reviews:
        text = (r.text or "").strip()[:MAX_REVIEW_CHARS]
        bullets.append(
            f"- ({r.semester.season} {r.semester.year},"
            f" {r.instructor_rating}/5 instructor, {r.difficulty}/5 difficulty,"
            f" {r.recommendability}/5 recommend): {text}"
        )
    return [
        {
            "role": "system",
            "content": (
                "You summarize university course reviews into clear, honest guidance. "
                "Write 3-5 sentences. Do not use headings or bullet points. "
                "Do not restate the course or instructor name. Do not invent details."
                "Match the tone and style of the reviews. Get straight to the point."
                f"Today's date is {datetime.now().strftime('%B %d, %Y')}."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Course: {course.code()} — {course.title}\n"
                f"Instructor: {instructor.full_name}\n\n"
                "Summarize these student reviews:\n" + "\n".join(bullets)
            ),
        },
    ]


class Command(BaseCommand):
    """Generate AI summaries for course-instructor pairs using OpenRouter."""

    help = "Generate AI review summaries via OpenRouter."

    def add_arguments(self, parser):
        parser.add_argument("--model", help="OpenRouter model ID (required)")
        parser.add_argument(
            "--limit", type=int, default=500, help="Max pairs to process (default: 500)"
        )
        parser.add_argument(
            "--missing-only",
            action="store_true",
            dest="missing_only",
            help="Only process pairs without an existing summary",
        )
        parser.add_argument(
            "--semester",
            type=str,
            default=None,
            dest="semester",
            help=(
                "Only pairs that taught this term (format: <year>_<season>, e.g. 2024_spring)"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Print what would be processed without calling the API",
        )

    def handle(self, *args, **options):
        model_id = options["model"]
        if not model_id:
            raise CommandError(
                "--model is required. Example: --model openai/gpt-4o-mini"
            )
        if not settings.OPENROUTER_API_KEY:
            raise CommandError("OPENROUTER_API_KEY is not set.")

        pairs = self._get_pairs(options)
        if not pairs:
            self.stdout.write(self.style.WARNING("No pairs matched the criteria."))
            return

        self.stdout.write(f"Processing {len(pairs)} pair(s)...")

        for row in pairs:
            course = Course.objects.get(pk=row["course_id"])
            instructor = Instructor.objects.get(pk=row["instructor_id"])

            if options["dry_run"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY RUN] {course.code()} / {instructor.full_name} "
                        f"({row['review_count']} reviews)"
                    )
                )
                continue

            reviews = list(
                Review.objects.filter(course=course, instructor=instructor)
                .exclude(text="")
                .filter(hidden=False, toxicity_rating__lt=settings.TOXICITY_THRESHOLD)
                .order_by("-created")[:MAX_REVIEW_COUNT]
            )
            messages = _build_messages(course, instructor, reviews)

            response = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": model_id, "messages": messages},
                timeout=60,
            )
            response.raise_for_status()
            summary_text = response.json()["choices"][0]["message"]["content"].strip()

            ReviewLLMSummary.objects.update_or_create(
                course=course,
                instructor=instructor,
                defaults={
                    "summary_text": summary_text,
                    "model_id": model_id,
                    "source_review_count": len(reviews),
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Saved: {course.code()} / {instructor.full_name} ({len(reviews)} reviews)"
                )
            )

    def _get_pairs(self, options):
        semester = _resolve_semester(options["semester"])
        qs = Review.objects.exclude(text="").filter(
            hidden=False, toxicity_rating__lt=settings.TOXICITY_THRESHOLD
        )
        if semester is not None:
            qs = qs.filter(
                course__section__semester=semester,
                course__section__instructors=F("instructor_id"),
            )
        qs = (
            qs.values("course_id", "instructor_id")
            .annotate(review_count=Count("id", distinct=True))
            .filter(review_count__gte=MIN_REVIEW_COUNT)
        )
        if options["missing_only"]:
            qs = qs.annotate(
                _has_summary=Exists(
                    ReviewLLMSummary.objects.filter(
                        course_id=OuterRef("course_id"),
                        instructor_id=OuterRef("instructor_id"),
                    )
                )
            ).filter(_has_summary=False)
        qs = qs.order_by("-review_count")[: options["limit"]]
        return list(qs)

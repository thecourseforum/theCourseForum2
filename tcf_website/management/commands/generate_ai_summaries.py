"""
Generate AI review summaries for course–instructor pairs via Amazon Bedrock.

Usage:
    python manage.py generate_ai_summaries --limit 5 --missing-only
    python manage.py generate_ai_summaries --semester 2024_spring --dry-run
    python manage.py generate_ai_summaries --model us.amazon.nova-pro-v1:0
"""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.db.models import Count, Exists, F, OuterRef
from tqdm import tqdm

from tcf_website.models import Course, Instructor, Review, ReviewLLMSummary, Semester

TIMEOUT = 60
MAX_REVIEW_CHARS = 1000
MIN_REVIEW_COUNT = 5  # minimum number of reviews to create summary
MAX_REVIEW_COUNT = 50  # maximum number of reviews to include in the prompt
WORKERS = 20
MAX_SUMMARY_TOKENS = 512


def create_client():
    """Create before starting workers; use the normal AWS credential chain."""
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.BEDROCK_REGION,
        config=Config(
            connect_timeout=TIMEOUT,
            read_timeout=TIMEOUT,
            max_pool_connections=WORKERS,
            retries={"mode": "adaptive", "total_max_attempts": 5},
        ),
    )


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
    system = [
        {
            "text": (
                "You summarize university course reviews into clear, honest guidance. "
                "Write 3-5 sentences. Do not use headings or bullet points. "
                "Do not restate the course or instructor name. Do not invent details."
                "Match the tone and style of the reviews. Get straight to the point."
                f"Today's date is {datetime.now().strftime('%B %d, %Y')}."
            ),
        }
    ]
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        f"Course: {course.code()} — {course.title}\n"
                        f"Instructor: {instructor.full_name}\n\n"
                        "Summarize these student reviews:\n" + "\n".join(bullets)
                    )
                }
            ],
        },
    ]
    return system, messages


def _summary_text_from_bedrock_response(response):
    """Only persist complete text responses, never blocked or truncated output."""
    if response.get("stopReason") != "end_turn":
        return None
    content = response["output"]["message"]["content"]
    text = "\n".join(block["text"] for block in content if "text" in block).strip()
    return text or None


def summarize_one(client, row, model_id, dry_run):
    """Summarize one pair. Returns (kind, message) or None on failure. Never raises."""
    try:
        course = Course.objects.get(pk=row["course_id"])
        instructor = Instructor.objects.get(pk=row["instructor_id"])

        if dry_run:
            return (
                "dry_run",
                f"[DRY RUN] {course.code()} / {instructor.full_name} "
                f"({row['review_count']} reviews)",
            )

        reviews = list(
            Review.objects.filter(course=course, instructor=instructor)
            .exclude(text="")
            .filter(hidden=False, toxicity_rating__lt=settings.TOXICITY_THRESHOLD)
            .order_by("-created")[:MAX_REVIEW_COUNT]
        )
        system, messages = _build_messages(course, instructor, reviews)

        response = client.converse(
            modelId=model_id,
            system=system,
            messages=messages,
            inferenceConfig={"maxTokens": MAX_SUMMARY_TOKENS},
        )
        summary_text = _summary_text_from_bedrock_response(response)
        if not summary_text:
            return None

        ReviewLLMSummary.objects.update_or_create(
            course=course,
            instructor=instructor,
            defaults={
                "summary_text": summary_text,
                "model_id": model_id,
                "source_review_count": len(reviews),
            },
        )

        return (
            "saved",
            f"Saved: {course.code()} / {instructor.full_name} ({len(reviews)} reviews)",
        )
    except (
        BotoCoreError,
        ClientError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        AttributeError,
        DatabaseError,
        ObjectDoesNotExist,
    ):
        return None


class Command(BaseCommand):
    """Management command: Bedrock-backed LLM summaries per course–instructor pair."""

    help = "Generate AI review summaries via Amazon Bedrock (Amazon Nova by default)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            default=settings.BEDROCK_MODEL_ID,
            help="Bedrock model or inference profile ID (default: BEDROCK_MODEL_ID)",
        )
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

    def _run_summaries_parallel(self, pairs, model_id, dry_run):
        client = None if dry_run else create_client()

        def _summarize(row):
            return summarize_one(client, row, model_id, dry_run)

        try:
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                return list(
                    tqdm(
                        pool.map(_summarize, pairs),
                        total=len(pairs),
                        desc="Summaries",
                    )
                )
        finally:
            if client is not None:
                client.close()

    def _report_pair_results(self, pairs, results):
        error_count = 0
        for row, result in zip(pairs, results, strict=True):
            if result is None:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"course_id={row['course_id']} "
                        f"instructor_id={row['instructor_id']}: failed"
                    )
                )
                continue
            kind, msg = result
            if kind == "dry_run":
                self.stdout.write(self.style.WARNING(msg))
            else:
                self.stdout.write(self.style.SUCCESS(msg))
        return error_count

    def handle(self, *args, **options):
        start = time.time()

        model_id = options["model"]
        if not model_id:
            raise CommandError(
                "Set BEDROCK_MODEL_ID or pass --model with a Bedrock ID."
            )

        pairs = self._get_pairs(options)
        if not pairs:
            self.stdout.write(self.style.WARNING("No pairs matched the criteria."))
            return

        self.stdout.write(f"Processing {len(pairs)} pair(s)...")

        try:
            results = self._run_summaries_parallel(pairs, model_id, options["dry_run"])
        except (BotoCoreError, ClientError) as exc:
            raise CommandError(f"Could not initialize Amazon Bedrock: {exc}") from exc
        error_count = self._report_pair_results(pairs, results)

        elapsed = time.time() - start
        ok = len(pairs) - error_count
        self.stdout.write(f"\nFinished {ok}/{len(pairs)} pair(s) in {elapsed:.1f}s")

        if error_count:
            raise CommandError(f"{error_count} pair(s) failed.")

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

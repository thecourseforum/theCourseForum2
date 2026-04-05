"""
Generate AI review summaries for course–instructor pairs via OpenRouter.

Usage:
    python manage.py generate_ai_summaries --model openai/gpt-4o-mini
    python manage.py generate_ai_summaries --model ... --semester 2024_spring --dry-run
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.db.models import Count, Exists, F, OuterRef
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from tcf_website.models import Course, Instructor, Review, ReviewLLMSummary, Semester

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = 60
MAX_REVIEW_CHARS = 1000
MIN_REVIEW_COUNT = 5  # minimum number of reviews to create summary
MAX_REVIEW_COUNT = 50  # maximum number of reviews to include in the prompt
# OpenRouter ~20 requests/minute (not 20 concurrent): space starts across all threads.
REQUESTS_PER_MINUTE = 20
MIN_REQUEST_INTERVAL = 60.0 / REQUESTS_PER_MINUTE
WORKERS = 20

_RATE_LOCK = threading.Lock()
_NEXT_SLOT_MONO = 0.0


def _wait_openrouter_slot():
    """Next OpenRouter request may start (global across worker threads)."""
    global _NEXT_SLOT_MONO
    with _RATE_LOCK:
        now = time.monotonic()
        if now < _NEXT_SLOT_MONO:
            time.sleep(_NEXT_SLOT_MONO - now)
            now = time.monotonic()
        _NEXT_SLOT_MONO = now + MIN_REQUEST_INTERVAL


def create_session():
    """Shared pool and retries for transient 5xx."""
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=WORKERS,
        pool_maxsize=WORKERS,
        max_retries=Retry(
            total=4,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset(["POST"]),
        ),
    )
    session.mount("https://", adapter)
    return session


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


def summarize_one(session, row, model_id, dry_run):
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
        messages = _build_messages(course, instructor, reviews)

        _wait_openrouter_slot()
        response = session.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": model_id, "messages": messages},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        choice0 = choices[0]
        if not isinstance(choice0, dict):
            return None
        message = choice0.get("message")
        if not isinstance(message, dict):
            return None
        raw_content = message.get("content")
        if not isinstance(raw_content, str):
            return None
        summary_text = raw_content.strip()
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
        requests.RequestException,
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
        start = time.time()

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

        session = create_session()
        model_id_kw = model_id
        dry_run_kw = options["dry_run"]

        def _summarize(row):
            return summarize_one(session, row, model_id_kw, dry_run_kw)

        # ── Call OpenRouter concurrently (starts are globally rate-limited) ──
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            results = list(
                tqdm(
                    pool.map(_summarize, pairs),
                    total=len(pairs),
                    desc="Summaries",
                )
            )

        error_count = 0
        for row, result in zip(pairs, results):
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

"""List reviews for a course/instructor page for moderation purposes.

Usage:
  docker exec -it tcf_django python manage.py list_reviews --url "/course/42/67/"
  docker exec -it tcf_django python manage.py list_reviews --course-id 42 --instructor-id 67

Outputs one REVIEW| line per review for machine parsing, plus human-readable headers.
"""

import re
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError

from tcf_website.models import Course, Instructor, Review


class Command(BaseCommand):
    help = "List reviews for a course/instructor page (for moderation)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            help='Review page URL, e.g. "https://thecourseforum.com/course/42/67/"',
        )
        parser.add_argument("--course-id", type=int, help="Course ID")
        parser.add_argument("--instructor-id", type=int, help="Instructor ID")

    def handle(self, *args, **options):
        course_id, instructor_id = self._resolve_ids(options)

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            raise CommandError(f"Course {course_id} not found")

        try:
            instructor = Instructor.objects.get(pk=instructor_id)
        except Instructor.DoesNotExist:
            raise CommandError(f"Instructor {instructor_id} not found")

        reviews = (
            Review.objects.filter(course=course, instructor=instructor)
            .select_related("user")
            .order_by("-created")
        )

        self.stdout.write(
            f"\nReviews for {course} taught by {instructor} "
            f"({reviews.count()} total)\n"
            + "-" * 60
        )

        if not reviews.exists():
            self.stdout.write("No reviews found.")
            return

        for review in reviews:
            user = review.user
            display_name = user.get_full_name() or user.username or user.email or "Unknown"
            email = user.email or ""
            hidden_flag = "[HIDDEN] " if review.hidden else ""
            excerpt = review.text[:120].replace("\n", " ").replace("|", " ").strip() if review.text else "(no text)"

            self.stdout.write(
                f"\n{hidden_flag}ID: {review.id} | {display_name} | {email} | {review.created.date()}"
            )
            self.stdout.write(f'  "{excerpt}"')

            # Machine-parseable line for hide_review.sh
            # Format: REVIEW|<id>|<display_name>|<email>|<hidden>|<excerpt>
            safe_name = display_name.replace("|", " ")
            safe_email = email.replace("|", " ")
            self.stdout.write(
                f"REVIEW|{review.id}|{safe_name}|{safe_email}|{review.hidden}|{excerpt}"
            )
            self.stdout.flush()

        self.stdout.write("\n" + "-" * 60)

    def _resolve_ids(self, options):
        if options.get("url"):
            return self._parse_url(options["url"])
        if options.get("course_id") and options.get("instructor_id"):
            return options["course_id"], options["instructor_id"]
        raise CommandError("Provide --url or both --course-id and --instructor-id")

    def _parse_url(self, url):
        path = urlparse(url).path
        match = re.search(r"/course/(\d+)/(\d+)", path)
        if not match:
            raise CommandError(
                f"Could not parse course/instructor IDs from URL: {url}\n"
                "Expected format: /course/<course_id>/<instructor_id>/"
            )
        return int(match.group(1)), int(match.group(2))

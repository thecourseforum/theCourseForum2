"""List reviews for a course/instructor page for moderation purposes.

Usage:
  docker exec -it tcf_django python manage.py list_reviews --url "/course/42/67/"
  docker exec -it tcf_django python manage.py list_reviews --course-id 42 --instructor-id 67

  By default, names and emails are masked. Pass --show-user-info to reveal them.
  Pass --parseable to emit REVIEW| lines for piping into hide_review.sh.

WARNING: With --show-user-info, output contains PII (names and email addresses).
Do not redirect to log files or CI/CD artifacts.
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
        parser.add_argument(
            "--show-user-info",
            action="store_true",
            default=False,
            help="Reveal full names and email addresses (outputs PII — do not log)",
        )
        parser.add_argument(
            "--hidden-only",
            action="store_true",
            default=False,
            help="Show only hidden reviews",
        )
        parser.add_argument(
            "--visible-only",
            action="store_true",
            default=False,
            help="Show only visible (non-hidden) reviews",
        )
        parser.add_argument(
            "--parseable",
            action="store_true",
            default=False,
            help="Emit REVIEW| lines for piping into hide_review.sh",
        )

    def handle(self, *args, **options):
        if options["hidden_only"] and options["visible_only"]:
            raise CommandError("--hidden-only and --visible-only are mutually exclusive")

        course_id, instructor_id = self._resolve_ids(options)

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist as err:
            raise CommandError(f"Course {course_id} not found") from err

        try:
            instructor = Instructor.objects.get(pk=instructor_id)
        except Instructor.DoesNotExist as err:
            raise CommandError(f"Instructor {instructor_id} not found") from err

        reviews = (
            Review.objects.filter(course=course, instructor=instructor)
            .select_related("user")
            .order_by("-created")
        )

        if options["hidden_only"]:
            reviews = reviews.filter(hidden=True)
        elif options["visible_only"]:
            reviews = reviews.filter(hidden=False)

        review_list = list(reviews)
        count = len(review_list)
        show_user_info = options["show_user_info"]
        parseable = options["parseable"]

        self.stdout.write(
            f"\nReviews for {course} taught by {instructor} "
            f"({count} total)\n"
            + "-" * 60
        )

        if not review_list:
            self.stdout.write("No reviews found.")
            return

        for review in review_list:
            user = review.user
            raw_name = user.get_full_name() or user.username or user.email or "Unknown"
            raw_email = user.email or ""
            hidden_flag = "[HIDDEN] " if review.hidden else ""
            excerpt = self._safe_field(review.text[:120]) if review.text else "(no text)"

            if show_user_info:
                display_name = self._safe_field(raw_name)
                display_email = self._safe_field(raw_email)
            else:
                display_name = self._mask_name(raw_name)
                display_email = self._mask_email(raw_email)

            self.stdout.write(
                f"\n{hidden_flag}ID: {review.id} | {display_name} | {display_email} | {review.created.date()}"
            )
            self.stdout.write(f'  "{excerpt}"')

            if parseable:
                # Format: REVIEW|<id>|<display_name>|<email>|<hidden>|<excerpt>
                self.stdout.write(
                    f"REVIEW|{review.id}|{display_name}|{display_email}|{review.hidden}|{excerpt}"
                )
            self.stdout.flush()

        self.stdout.write("\n" + "-" * 60)

    def _safe_field(self, value: str) -> str:
        return value.replace("|", " ").replace("\n", " ").strip()

    def _mask_name(self, name: str) -> str:
        parts = name.split()
        if not parts:
            return "***"
        if len(parts) == 1:
            return parts[0][0] + "***" if parts[0] else "***"
        return parts[0][0] + "*** " + parts[-1][0] + "***"

    def _mask_email(self, email: str) -> str:
        if not email or "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        return local[0] + "***@" + domain if local else "***@" + domain

    def _resolve_ids(self, options):
        if options.get("url"):
            return self._parse_url(options["url"])
        if options.get("course_id") is not None and options.get("instructor_id") is not None:
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

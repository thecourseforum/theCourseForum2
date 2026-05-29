"""Hide (soft-delete) or unhide a review by ID.

Usage:
  # Show review details without making changes
  python manage.py hide_review --id 42 --show

  # Hide a review
  python manage.py hide_review --id 42 --reason "Violates community guidelines"

  # Unhide a review
  python manage.py hide_review --id 42 --reason "Mistakenly hidden" --unhide
"""

import datetime

from django.core.management.base import BaseCommand, CommandError

from tcf_website.models import Review


class Command(BaseCommand):
    help = "Hide or unhide a review by ID (soft-delete)"

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, required=True, help="Review ID")
        parser.add_argument(
            "--reason",
            type=str,
            help="Reason for hiding/unhiding (required unless --show)",
        )
        parser.add_argument(
            "--show",
            action="store_true",
            help="Print full review and exit without changes",
        )
        parser.add_argument(
            "--unhide",
            action="store_true",
            help="Unhide the review instead of hiding it",
        )

    def handle(self, *args, **options):
        review_id = options["id"]
        reason = options.get("reason")
        show_only = options["show"]
        unhide = options["unhide"]

        try:
            review = Review.objects.select_related(
                "user", "course", "instructor", "semester"
            ).get(pk=review_id)
        except Review.DoesNotExist as err:
            raise CommandError(f"Review {review_id} not found") from err

        self._print_review(review)

        if show_only:
            return

        if not reason:
            raise CommandError(
                "--reason is required. State why this review is being hidden/unhidden."
            )

        target_hidden = not unhide
        action = "unhide" if unhide else "hide"

        if review.hidden == target_hidden:
            state = "hidden" if review.hidden else "visible"
            self.stdout.write(
                f"Review {review_id} is already {state}. No changes made."
            )
            return

        review.hidden = target_hidden
        review.save(update_fields=["hidden"])

        ts = datetime.datetime.now(datetime.UTC).isoformat()
        self.stdout.write(
            f"\n[HIDE_REVIEW] id={review_id} hidden={target_hidden} "
            f'action={action} reason="{reason}" at={ts}'
        )
        self.stdout.write(
            f"Done. Review {review_id} is now {'hidden' if target_hidden else 'visible'}."
        )

    def _print_review(self, review):
        user = review.user
        display_name = user.get_full_name() or user.username or user.email or "Unknown"

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"Review ID : {review.id}")
        self.stdout.write(f"Status    : {'HIDDEN' if review.hidden else 'visible'}")
        self.stdout.write(f"User      : {display_name}")
        self.stdout.write(f"Email     : {user.email or '(none)'}")
        self.stdout.write(f"Course    : {review.course}")
        self.stdout.write(f"Instructor: {review.instructor}")
        self.stdout.write(f"Semester  : {review.semester}")
        self.stdout.write(f"Created   : {review.created}")
        self.stdout.write(f"Text      :\n{review.text or '(no text)'}")
        self.stdout.write("=" * 60)
        self.stdout.flush()

"""Print weekly review inflow and current-term coverage."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone

from tcf_website.models import Review, Section
from tcf_website.utils import reviewable_semesters

COVERAGE_MIN_REVIEWS = 3


class Command(BaseCommand):
    """Usage: `uv run python manage.py review_metrics --weeks 8`"""

    help = "Weekly course-review counts (text vs ratings-only) and coverage."

    def add_arguments(self, parser):
        parser.add_argument("--weeks", type=int, default=8)

    def handle(self, *args, **options):
        now = timezone.now()
        for back in range(options["weeks"], 0, -1):
            start = now - timedelta(weeks=back)
            end = start + timedelta(weeks=1)
            # Aliases must not be named "text": that field is what the filters
            # below match on, and Django resolves aggregate() kwargs against a
            # query that already carries earlier aliases as annotations, so an
            # alias named "text" shadows the Review.text field for any later
            # aggregate's filter=Q(text=...) in the same call.
            row = Review.objects.filter(
                course__isnull=False, created__gte=start, created__lt=end
            ).aggregate(
                text_count=Count("id", filter=~Q(text="")),
                ratings_only_count=Count("id", filter=Q(text="")),
            )
            self.stdout.write(
                f"{start:%Y-%m-%d}  text={row['text_count']}  "
                f"ratings_only={row['ratings_only_count']}"
            )
        self._write_coverage()

    def _write_coverage(self):
        semester = reviewable_semesters().order_by("-number").first()
        if semester is None:
            self.stdout.write("coverage: no started semester")
            return
        offered = set(
            Section.objects.filter(semester=semester, instructors__isnull=False)
            .values_list("course_id", "instructors__id")
            .distinct()
        )
        well_reviewed = set(
            Review.objects.filter(
                hidden=False,
                course__isnull=False,
                toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
            )
            .values("course_id", "instructor_id")
            .annotate(n=Count("id"))
            .filter(n__gte=COVERAGE_MIN_REVIEWS)
            .values_list("course_id", "instructor_id")
        )
        covered = len(offered & well_reviewed)
        self.stdout.write(
            f"coverage: {covered}/{len(offered)} pairs offered in {semester} "
            f"have {COVERAGE_MIN_REVIEWS}+ reviews"
        )

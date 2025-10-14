"""
Update instructor archived status based on current semester teaching.

Usage:
python manage.py update_archived_status
OR
docker exec -it tcf_django python manage.py update_archived_status
"""

import time
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from tcf_website.models import Instructor, Section, Semester


class Command(BaseCommand):
    """Django management command to update instructor archived status."""

    help = (
        "Updates instructor archived status based on whether they are "
        "teaching in the current semester"
    )

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--semester",
            type=str,
            help='Semester number (e.g., "1242" for Spring 2024). Defaults to latest semester for archived status update.',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        start_time = time.time()

        # Get semester for archived status update
        if options["semester"]:
            try:
                semester = Semester.objects.get(number=options["semester"])
            except Semester.DoesNotExist:
                print(f"Semester {options['semester']} not found")
                return
        else:
            semester = Semester.latest()

        print(f"Updating archived status for semester: {semester}")

        instructors = Instructor.objects.all()
        total_instructors = instructors.count()
        print(f"Found {total_instructors} instructors")

        # Process instructors and track counts
        counts = self._process_instructors(instructors, semester)

        elapsed_time = time.time() - start_time
        self._print_results(counts, total_instructors, elapsed_time)

    def _process_instructors(self, instructors, semester):
        """Process instructors and return counts."""
        archived_count = 0
        active_count = 0
        updated_count = 0

        try:
            with transaction.atomic():
                for instructor in tqdm(instructors, desc="Processing instructors"):
                    is_teaching_current = Section.objects.filter(
                        instructors=instructor,
                        semester=semester
                    ).exists()

                    should_be_archived = not is_teaching_current

                    if instructor.is_archived != should_be_archived:
                        instructor.is_archived = should_be_archived
                        instructor.save(update_fields=['is_archived'])
                        status = "ARCHIVED" if should_be_archived else "ACTIVATED"
                        print(f"  {instructor.full_name}: {status}")
                        updated_count += 1

                    if should_be_archived:
                        archived_count += 1
                    else:
                        active_count += 1

        except (ValueError, TypeError, AttributeError,
                transaction.TransactionManagementError) as e:
            print(f"Error processing instructors: {e}")
            raise

        return {
            'archived': archived_count,
            'active': active_count,
            'updated': updated_count
        }

    def _print_results(self, counts, total_instructors, elapsed_time):
        """Print the final results."""
        print("\nSuccessfully updated archived status!")
        print(f"Total instructors: {total_instructors}")
        print(f"Updated: {counts['updated']}")
        print(f"Archived: {counts['archived']}")
        print(f"Active: {counts['active']}")
        print(f"Total time: {elapsed_time:.2f} seconds")

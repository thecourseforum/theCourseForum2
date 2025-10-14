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

    help = "Updates instructor archived status based on whether they are teaching in the current semester"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--semester",
            type=str,
            help='Semester number (e.g., "1242" for Spring 2024). Defaults to latest semester.',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        start_time = time.time()

        # Use provided semester or get latest
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

        except Exception as e:
            print(f"Error processing instructors: {e}")
            return

        elapsed_time = time.time() - start_time

        print(f"\nSuccessfully updated archived status!")
        print(f"Total instructors: {total_instructors}")
        print(f"Updated: {updated_count}")
        print(f"Archived: {archived_count}")
        print(f"Active: {active_count}")
        print(f"Total time: {elapsed_time:.2f} seconds")

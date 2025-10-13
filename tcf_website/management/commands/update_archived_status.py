"""Management command to update instructor archived status based on current semester teaching."""

from django.core.management.base import BaseCommand
from django.db import transaction

from tcf_website.models import Instructor, Section, Semester


class Command(BaseCommand):
    help = "Update instructor archived status based on whether they are teaching in the current semester"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        latest_semester = Semester.latest()
        
        self.stdout.write(
            self.style.SUCCESS(f"Updating archived status for semester: {latest_semester}")
        )

        instructors = Instructor.objects.all()
        total_instructors = instructors.count()
        
        archived_count = 0
        active_count = 0

        with transaction.atomic():
            for instructor in instructors:
                is_teaching_current = Section.objects.filter(
                    instructors=instructor,
                    semester=latest_semester
                ).exists()
                
                should_be_archived = not is_teaching_current
                
                if instructor.is_archived != should_be_archived:
                    if dry_run:
                        status = "WOULD BE ARCHIVED" if should_be_archived else "WOULD BE ACTIVATED"
                        self.stdout.write(
                            f"  {instructor.full_name}: {status}"
                        )
                    else:
                        instructor.is_archived = should_be_archived
                        instructor.save(update_fields=['is_archived'])
                        status = "ARCHIVED" if should_be_archived else "ACTIVATED"
                        self.stdout.write(
                            f"  {instructor.full_name}: {status}"
                        )
                
                if should_be_archived:
                    archived_count += 1
                else:
                    active_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDRY RUN - No changes made\n"
                    f"Total instructors: {total_instructors}\n"
                    f"Would be archived: {archived_count}\n"
                    f"Would be active: {active_count}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully updated archived status!\n"
                    f"Total instructors: {total_instructors}\n"
                    f"Archived: {archived_count}\n"
                    f"Active: {active_count}"
                )
            )

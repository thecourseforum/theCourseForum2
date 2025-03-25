import collections
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm
from tcf_website.models import Instructor, Section, Review, CourseInstructorGrade, Question


class Command(BaseCommand):
    help = "Merges duplicate instructors with the same first word in first name and same last name"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without making changes",
        )

    def handle(self, *args, **options):
        self.verbose = options["verbose"]
        self.dry_run = options["dry_run"]

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("Running in dry-run mode - no changes will be made")
            )

        # Group instructors by first word of first name and last name
        name_groups = collections.defaultdict(list)

        all_instructors = Instructor.objects.all()
        self.stdout.write(f"Total instructors: {all_instructors.count()}")

        for instructor in tqdm(all_instructors, desc="Grouping instructors"):
            if not instructor.last_name or not instructor.first_name:
                continue  # Skip instructors with no last name or first name

            # Get first word of first name
            first_name_parts = instructor.first_name.strip().split()
            if not first_name_parts:
                continue

            first_word = first_name_parts[0].lower()
            last_name = instructor.last_name.lower()

            if last_name == "dukes":
                continue

            # Create a key that combines first word of first name and last name
            name_key = (first_word, last_name)
            name_groups[name_key].append(instructor)

        # Count duplicate groups
        duplicate_groups = {k: v for k, v in name_groups.items() if len(v) > 1}
        self.stdout.write(
            f"Found {len(duplicate_groups)} groups with potential duplicate instructors"
        )

        # Process duplicate instructors
        processed_count = 0
        merged_count = 0

        for name_key, instructors in tqdm(duplicate_groups.items(), desc="Processing duplicates"):
            # Display all duplicate instructors in this group
            first_word, last_name = name_key
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nPotential duplicates with first name starting with '{first_word}' and last name '{last_name}':"
                )
            )

            for i, instructor in enumerate(instructors, 1):
                # Count sections, reviews, and grades for this instructor
                section_count = Section.objects.filter(instructors=instructor).count()
                review_count = Review.objects.filter(instructor=instructor).count()
                grade_count = CourseInstructorGrade.objects.filter(instructor=instructor).count()
                question_count = Question.objects.filter(instructor=instructor).count()

                # Show additional instructor info
                email_info = f", Email: '{instructor.email}'" if instructor.email else ""
                hidden_info = ", Hidden: Yes" if instructor.hidden else ""
                dept_count = instructor.departments.count()
                dept_info = f", Departments: {dept_count}" if dept_count else ""

                self.stdout.write(
                    f"  #{i}: ID={instructor.id}, Full name: '{instructor.full_name}'{email_info}{hidden_info}{dept_info}, "
                    f"Sections: {section_count}, Reviews: {review_count}, Grades: {grade_count}, Questions: {question_count}"
                )

            processed_count += 1

            # Skip if only one instructor in group (should not happen, but just in case)
            if len(instructors) <= 1:
                continue

            # Sort instructors by ID, highest (most recent) first
            instructors.sort(key=lambda i: i.id, reverse=True)

            keep_instructor = instructors[0]
            duplicate_instructors = [i for i in instructors if i != keep_instructor]

            self.stdout.write(f"\n  Action plan:")
            self.stdout.write(
                f"    KEEP: ID={keep_instructor.id}, '{keep_instructor.full_name}' (most recent)"
            )

            for dup in duplicate_instructors:
                self.stdout.write(f"    MERGE: ID={dup.id}, '{dup.full_name}' into kept instructor")

            if not self.dry_run:
                with transaction.atomic():  # Ensure all operations succeed or fail together
                    for dup_instructor in duplicate_instructors:
                        # Get the existing sections for the kept instructor
                        existing_sections = set(
                            Section.objects.filter(instructors=keep_instructor).values_list(
                                "id", flat=True
                            )
                        )

                        # Transfer sections to the kept instructor (avoiding duplicates)
                        section_count = 0
                        for section in Section.objects.filter(instructors=dup_instructor):
                            # Only add if the kept instructor isn't already associated
                            if section.id not in existing_sections:
                                section.instructors.add(keep_instructor)
                                existing_sections.add(section.id)
                                section_count += 1
                            section.instructors.remove(dup_instructor)

                        # Transfer all reviews to the kept instructor
                        review_count = Review.objects.filter(instructor=dup_instructor).update(
                            instructor=keep_instructor
                        )

                        # Transfer all questions to the kept instructor
                        question_count = Question.objects.filter(instructor=dup_instructor).update(
                            instructor=keep_instructor
                        )

                        # Transfer all course grades to the kept instructor
                        grade_count = CourseInstructorGrade.objects.filter(
                            instructor=dup_instructor
                        ).update(instructor=keep_instructor)

                        # Get existing departments for the kept instructor
                        existing_departments = set(
                            keep_instructor.departments.values_list("id", flat=True)
                        )

                        # Transfer departments (avoiding duplicates)
                        dept_count = 0
                        for dept in dup_instructor.departments.all():
                            if dept.id not in existing_departments:
                                keep_instructor.departments.add(dept)
                                existing_departments.add(dept.id)
                                dept_count += 1

                        # Log what was transferred
                        self.stdout.write(
                            f"      Transferred {section_count} sections, {review_count} reviews, "
                            f"{grade_count} grade records, {question_count} questions, and {dept_count} departments "
                            f"from {dup_instructor.full_name}"
                        )

                        # Delete the duplicate instructor
                        dup_instructor.delete()

                        merged_count += 1

                self.stdout.write(self.style.SUCCESS("    ✓ Merge completed successfully"))

        self.stdout.write(self.style.SUCCESS(f"\nSummary:"))
        self.stdout.write(
            f"- Examined {processed_count} instructor groups with potential duplicates"
        )
        self.stdout.write(f"- Merged {merged_count} duplicate instructors")

        if self.dry_run:
            self.stdout.write(self.style.WARNING("This was a dry run, no changes were made"))

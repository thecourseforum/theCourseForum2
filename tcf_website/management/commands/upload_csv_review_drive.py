import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand

from tcf_website.models import *

DATA_DIR = "tcf_website/management/commands/review_drive_responses/"


class Command(BaseCommand):

    # Run this coomand using `sudo docker exec -it tcf_django python3 manage.py upload_csv_review_drive [filename] [season] [year]`
    # Optional flag --verbose can be set to show output of the script
    # Must be run in a separate terminal after already running docker-compose up
    # May have to restart the docker container for database changes to be visible on the site
    # Visually check that CS department has been moved to E School and that
    # other schools have been split up.

    help = (
        "Uploads CSV from /review_drive_responses/ in the format of Time, Email, Mnemonic, Number, Name, Review, "
        "Rating, Enjoyable, Recommendation, Difficulty, Reading Hours, Writing Hours, Group work Hours, Misc Hours"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            help=(
                "Filepath of csv to upload in /review_drive_responses/"
                "Must be in correct format."
            ),
            type=str,
        )
        parser.add_argument(
            "season",
            help=(
                "What season the reviews took place i.e. Fall, January, Spring, Summer"
            ),
            type=str,
        )
        parser.add_argument(
            "year",
            help=("Year of reviews i.e. 2024"),
            type=int,
        )

        # Named (optional) arguments
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output",
        )

    def handle(self, *args, **options):
        verbose = options["verbose"]
        filename = options["filename"]
        season = options["season"]
        year = options["year"]

        # Get semester object from args
        semester = Semester.objects.filter(
            season=season.upper(), year=year
        ).first()
        if semester.count() <= 0:
            print("ERROR: Semester not found")
            return

        # Needs to be created ahead of time in the db
        dummy_account = User.objects.filter(computing_id__iexact="reviewdrive")
        if dummy_account.count() <= 0:
            print("ERROR: DUMMY ACCOUNT NOT FOUND")
            return

        if verbose:
            print("Starting file upload...")

        file = open(os.path.join(DATA_DIR, filename), mode="r")
        csv_file = csv.reader(file)

        for i, line in enumerate(csv_file):
            if i == 0:
                continue

            # Strip needed to remove random whitespace for exact match
            email = line[1].strip()
            mnemonic = line[2].strip()
            num = int(line[3].strip())
            instructor_arr = line[4].strip().split(" ", 1)

            if verbose:
                print(email, mnemonic, num, instructor)

            # Use account if found. Otherwise, use dummy user
            account = User.objects.filter(email=email).first()
            if account is not None and verbose:
                print("Account already found for", email)
            elif account is None:
                account = dummy_account.first()

            subdepartment = Subdepartment.objects.filter(
                mnemonic__iexact=mnemonic
            ).first()
            if subdepartment is None:
                print(
                    "Subdepartment not found for",
                    mnemonic,
                    num,
                    email,
                    instructor,
                    "skipping...",
                )
                continue

            course = Course.objects.filter(
                subdepartment=subdepartment, number=num
            ).first()
            if course is None:
                print(
                    "Course not found for",
                    mnemonic,
                    num,
                    email,
                    instructor,
                    "skipping...",
                )
                continue
            if verbose:
                print(subdepartment, course)

            # Use only last name if list is size of 1
            # Some professors only have last name in the database
            if len(instructor_arr) > 1:
                instructor = Instructor.objects.filter(
                    first_name__iexact=instructor_arr[0],
                    last_name__iexact=instructor_arr[1],
                ).first()
            else:
                instructor = Instructor.objects.filter(
                    last_name__iexact=instructor_arr[0]
                ).first()

            if instructor is None:
                print(
                    "Instructor not found for",
                    mnemonic,
                    num,
                    email,
                    instructor,
                    "skipping...",
                )
                continue

            review_content = line[5].strip()

            # Confirm the review is not already in the database
            if Review.objects.filter(text__iexact=review_content).count() > 0:
                print(
                    "REVIEW ALREADY IN DATABASE FOR",
                    mnemonic,
                    num,
                    email,
                    instructor,
                    "skipping...",
                )
                continue

            # CSV must be formatted EXACTLY in order
            instructor_rating = int(line[6].strip())
            enjoyability = int(line[7].strip())
            recommendability = int(line[8].strip())
            difficulty = int(line[9].strip())
            amount_reading = int(line[10].strip())
            amount_writing = int(line[11].strip())
            amount_group = int(line[12].strip())
            amount_homework = int(line[13].strip())
            hours_per_week = (
                amount_reading + amount_writing + amount_group + amount_homework
            )

            created = datetime.strptime(line[0].strip(), "%m/%d/%Y %H:%M:%S")
            modified = datetime.now()

            if account == dummy_account.first():
                review_email = email
            else:
                review_email = ""

            review = Review(
                text=review_content,
                user=account,
                course=course,
                instructor=instructor,
                semester=semester,
                instructor_rating=instructor_rating,
                difficulty=difficulty,
                recommendability=recommendability,
                enjoyability=enjoyability,
                hours_per_week=hours_per_week,
                amount_reading=amount_reading,
                amount_writing=amount_writing,
                amount_group=amount_group,
                amount_homework=amount_homework,
                created=created,
                modified=modified,
                email=review_email,
            )
            review.save()

            if verbose:
                print("Finished row", i)

        print("All done!")

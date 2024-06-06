"""Command for uploading CSV review drive files to the database."""

# pylint: disable=no-member, too-many-locals, too-many-branches, too-many-statements

import csv
import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from tcf_website.models import (
    Course,
    Instructor,
    Review,
    Semester,
    Subdepartment,
    User,
)

DATA_DIR = "tcf_website/management/commands/review_drives/"


class Command(BaseCommand):
    """Command that is run for CSV upload."""

    # Run this command using
    # `docker exec -it tcf_django python3 manage.py load_review_drive <params>`
    # Required parameters: [filename]
    # Optional flag --verbose can be set to show output of the script
    # Must be run in a separate terminal after already running docker-compose up
    # May have to restart the docker container for database changes to be visible on the site

    help = (
        "Uploads CSV from /review_drives/ in the format of "
        "Time, Email, Mnemonic, Number, Name, Review, Rating, Enjoyable, Recommendation, "
        "Difficulty, Reading Hours, Writing Hours, Group work Hours, Misc Hours"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "semester",
            help=(
                "Semester name of csv to upload in /review_drives/"
                "Must be in format <YYYY>_<SEASON>"
            ),
            type=str,
        )

        # Named (optional) arguments
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output",
        )

    def handle(self, *args, **options):
        verbose = options["verbose"]
        semester: str = options["semester"]

        if semester.endswith(".csv"):
            semester = semester[: -len(".csv")]
        split = semester.split("_")
        year, season = int(split[0]), split[1].lower()

        # Get semester object from args
        semester = Semester.objects.filter(
            season=season.upper(), year=year
        ).first()
        if semester is None:
            print("ERROR: Semester not found")
            return

        # Needs to be created ahead of time in the db
        dummy_account = User.objects.filter(
            computing_id__iexact=settings.REVIEW_DRIVE_ID
        ).first()
        if dummy_account is None:
            dummy_account = User.objects.create_user(
                computing_id=settings.REVIEW_DRIVE_ID,
                graduation_year=year,
                username=settings.REVIEW_DRIVE_ID,
                password=settings.REVIEW_DRIVE_PASSWORD,
                email=settings.REVIEW_DRIVE_EMAIL,
                first_name="Review",
                last_name="Drive",
            )

        print("Starting file upload...")
        create_reviews(verbose, f"{year}_{season}.csv", semester, dummy_account)


def create_reviews(verbose, filename, semester, dummy_account):
    """Creates reviews based on CSV info."""
    with open(
        os.path.join(DATA_DIR, filename), mode="r", encoding="utf-8"
    ) as file:
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
                print(email, mnemonic, num, instructor_arr)

            # Use account if found. Otherwise, use dummy user
            account = User.objects.filter(email=email).first()
            if account is not None and verbose:
                print("Account already found for", email)
            elif account is None:
                account = dummy_account

            subdepartment = Subdepartment.objects.filter(
                mnemonic__iexact=mnemonic
            ).first()
            if subdepartment is None:
                print(
                    "Subdepartment not found for",
                    mnemonic,
                    num,
                    email,
                    instructor_arr,
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
                    instructor_arr,
                    "skipping...",
                )
                continue

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
                    instructor_arr,
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
                    instructor_arr,
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
                email=email if account == dummy_account else "",
            )
            review.save()

            if verbose:
                print("Finished row", i)

        print("All done!")

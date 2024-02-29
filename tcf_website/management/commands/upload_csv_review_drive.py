from django.core.management.base import BaseCommand, CommandError

from tcf_website.models import *
import csv
import os

DATA_DIR = "tcf_website/management/commands/review_drive_responses/"

class Command(BaseCommand):

    # Run this coomand using `sudo docker exec -it tcf_django python3 manage.py upload_csv_review_drive [filename] [season] [year]`
    # Optional flag --verbose can be set to show output of the script
    # Must be run in a separate terminal after already running docker-compose up
    # May have to restart the docker container for database changes to be visible on the site
    # Visually check that CS department has been moved to E School and that
    # other schools have been split up.

    help = "Uploads CSV from /review_drive_responses/ in the format of Time, Email, Mnemonic, Number, Name, Review, " \
           "Rating, Enjoyable, Recommendation, Difficulty, Reading Hours, Writing Hours, Group work Hours, Misc Hours"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            help=(
                'Filepath of csv to upload in /review_drive_responses/'
                "Must be in correct format."
            ),
            type=str,
        )
        parser.add_argument(
            "season",
            help=(
                'What season the reviews took place i.e. Fall, January, Spring, Summer'
            ),
            type=str,
        )
        parser.add_argument(
            "year",
            help=(
                'Year of reviews i.e. 2024'
            ),
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

        semester_query = Semester.objects.filter(season=season.upper(), year=year)
        if semester_query.count() <= 0:
            print('ERROR: Semester not found')
            return
        semester = semester_query.first()

        if verbose:
            print('Starting file upload...')
        file = open(os.path.join(DATA_DIR, filename), mode='r')
        csv_file = csv.reader(file)

        for i, line in enumerate(csv_file):
            if i == 0:
                continue

            email = line[1].strip()
            mnemonic = line[2].strip()
            num = int(line[3].strip())

            if verbose:
                print(email, mnemonic, num)

            account_query = User.objects.filter(email=email)
            if account_query.count() > 0:
                print('Account already found for', email)
            subdepartment_query = Subdepartment.objects.filter(mnemonic__iexact=mnemonic)
            if subdepartment_query.count() <= 0:
                print('Subdepartment not found for', mnemonic, num, email, 'skipping...')
                continue
            course_query = Course.objects.filter(subdepartment=subdepartment_query.first(), number=num)
            if course_query.count() <= 0:
                print('Course not found for', mnemonic, num, email, 'skipping...')
                continue
            if verbose:
                print(subdepartment_query.first(), course_query.first())

            if verbose:
                print('Finished row', i)

        print('All done!')

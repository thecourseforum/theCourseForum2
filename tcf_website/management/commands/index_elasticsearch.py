"""Management command that loads courses and instructors into Elasticsearch"""
from datetime import datetime

import os
import json
import requests

from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import Course, Instructor


class Command(BaseCommand):
    """Indexes the Elastic AppSearch instance w/ Course and Instructor data.

    Author: Bradley Knaysi

    Created: April 19th, 2020

    How To Use:

        $ cd theCourseForum2/
        $ docker-compose up

        open a new terminal

        $ cd theCourseForum2/
        $ docker exec -it tcf_django bash
        $ python3 manage.py index_elasticsearch

    WARNING: This should only be done by an Executive Team member each semester
    after new course and instructor data are added to the tcf_db. Note that the
    Elastic portal takes 1 to 2 minutes to fully reflect changes. You can run this as
    many times as you want! It updates a document in Elastic if it already exists and
    adds the document if it didn't. Additionally, this can only be run from a production
    environment due to its reliance on production environment variables (tcf secrets).

    """

    help = 'Indexes the Elastic AppSearch instance w/ Course and Instructor data.'

    def handle(self, *args, **options):

        courses_engine_endpoint = os.environ['ES_COURSE_DOCUMENTS_ENDPOINT']
        instructors_engine_endpoint = os.environ['ES_INSTRUCTOR_DOCUMENTS_ENDPOINT']
        all_courses = Course.objects.all().order_by('pk')
        all_instructors = Instructor.objects.all().order_by('pk')
        self.stdout.write("Number of Courses: " + str(len(all_courses)))
        self.stdout.write("Number of Instructors: " +
                          str(len(all_instructors)))

        batch_size = 100  # MUST NOT EXCEED 100
        documents = []
        count = 0
        current_year = datetime.now().year

        # Debug variables
        start = 0
        end = start

        for course in all_courses:

            end += 1

            # ignore courses not taught in the last 5 years
            if course.semester_last_taught.year < (current_year - 5):
                continue

            document = {
                "id": course.pk,
                "title": course.title,
                "description": course.description,
                "number": course.number,
                "mnemonic": course.code(),
                "review_count": course.review_count()
            }
            documents.append(document)
            count += 1

            # Send courses to API in groups
            if count == batch_size:
                self.post(documents, courses_engine_endpoint)
                count = 0
                documents.clear()

                # For debug
                self.stdout.write(
                    "Indexed Courses " +
                    str(start) +
                    " - " +
                    str(end))
                start = end

        # Handle remaining documents
        if len(documents) > 0:
            self.post(documents, courses_engine_endpoint)
            self.stdout.write("Indexed Courses " +
                              str(start) + " - " + str(end))

        # Reset
        documents.clear()
        count = 0
        start = 0
        end = batch_size

        for instructor in all_instructors:

            document = {
                "id": instructor.pk,
                "first_name": instructor.first_name,
                "last_name": instructor.last_name,
                "email": instructor.email,
                "website": instructor.website,
            }
            documents.append(document)
            count += 1

            # Send instructors to API in groups
            if count == batch_size:
                self.post(documents, instructors_engine_endpoint)
                count = 0
                documents.clear()

                # For debug
                self.stdout.write(
                    "Indexed Instructors " +
                    str(start) +
                    " - " +
                    str(end))
                start = end
                end += batch_size

        # Handle remaining documents
        if len(documents) > 0:
            self.post(documents, instructors_engine_endpoint)
            self.stdout.write("Indexed Instructors " +
                              str(start) + " - " + str(start + count))

    def post(self, documents, api_endpoint):
        """Posts documents to a Document API endpoint"""

        api_key = os.environ['ES_PRIVATE_API_KEY']
        https_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        }

        # Convert list to json string
        json_documents = json.dumps(documents)

        try:
            response = requests.post(
                url=api_endpoint,
                data=json_documents,
                headers=https_headers
            )
            if response.status_code != 200:
                raise CommandError("status_code = " +
                                   str(response.status_code) +
                                   " -- " +
                                   str(response.text))

        except Exception as error:
            raise CommandError("Error: " + str(error))

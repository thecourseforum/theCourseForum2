"""
Modules used
"""
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

    help = 'Indexes / Updates the Elastic-hosted cluster'

    def handle(self, *args, **options):

        # Set API endpoint
        courses_engine_endpoint = os.environ['ES_COURSE_ENDPOINT']

        all_courses = Course.objects.all().order_by('pk')
        self.stdout.write("Number of Courses: " + str(len(all_courses)))

        # Batch parameters
        documents = []
        batch_size = 100 # MUST NOT EXCEED 100
        start = 0
        end = batch_size
        count = 0
        for course in all_courses:

            document = {
                "id" : course.pk,
                "title" : course.title,
                "description" : course.description,
                "number" : course.number
            }

            # Add document
            documents.append(document)
            count += 1

            # Batching requests for efficiency
            if count == batch_size:

                # POST to Elastic
                self.post(documents, courses_engine_endpoint)

                # Prepare next batch
                count = 0
                start = end
                end += batch_size
                documents.clear()

        # Handle remaining documents
        if len(documents) > 0:

            # Set API endpoint
            courses_engine_endpoint = os.environ['ES_COURSE_ENDPOINT']

            # POST to Elastic
            self.post(documents, courses_engine_endpoint)


    def post(self, documents, api_endpoint):
        """Post document to a Document API
        """

        api_key = os.environ['ES_API_KEY']

        https_headers = {
            "Content-Type" : "application/json",
            "Authorization" : "Bearer " + api_key
        }

        # Convert list to json string
        json_documents = json.dumps(documents)

        try:
            # Send documents to the Elastic endpoint
            response = requests.post(
                url=api_endpoint,
                data=json_documents,
                headers=https_headers
            )
            self.stdout.write("status_code = " + str(response.status_code))

        except Exception as error:
            raise CommandError("Elastic indexing error: " + str(error))

"""
Modules used
"""
import json
import requests

from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import Course, Instructor

class Command(BaseCommand):
    """Indexes the Elastic AppSearch instance w/ Course and Instructor.

    Author: Bradley Knaysi

    Created: April 19th, 2020

    How To Use:

        $ cd theCourseForum2/
        $ docker-compose up

        open a new terminal

        $ cd theCourseForum2/
        $ docker exec -it tcf_django bash
        $ python3 manage.py index_elasticsearch

    WARNING: This should only be done by an Executive Team member once a semester
    after new course and instructor data are added to the tcf_db. Also the Elastic AppSearch
    portal takes like 10 minutes to fully update so be patient there.

    """

    help = 'Erases and re-indexes the Elastic hosted Elasticsearch cluster'

    def handle(self, *args, **options):

        courses_engine_endpoint = 'https://1761244fa3674318b11f8d5729ffd7a2.app-search.us-east4.gcp.elastic-cloud.com/api/as/v1/engines/uva-courses/documents'

        # PRIVATE READ / WRITE KEY (need to find more secret place)
        api_key = 'private-tw8dxda1rfxw28s7dxc6vihs'

        https_headers = {
            "Content-Type" : "application/json",
            "Authorization" : "Bearer " + api_key
        }

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
                try:

                    # Convert list to json string
                    json_documents = json.dumps(documents)

                    # Send documents to the Elastic endpoint
                    response = requests.post(
                        url=courses_engine_endpoint,
                        data=json_documents,
                        headers=https_headers
                    )
                    self.stdout.write("Indexed courses: " + str(start) + " - " + str(end) + "   status_code=" + str(response.status_code))

                    # Prepare next batch
                    count = 0
                    start = end
                    end += batch_size
                    documents.clear()

                except Exception as error:
                    raise CommandError("Elastic indexing error: " + str(error))

        # Handle remaining documents
        if len(documents) > 0:
            try:

                # Convert list to json string
                json_documents = json.dumps(documents)

                # Send documents to the Elastic endpoint
                response = requests.post(
                    url=courses_engine_endpoint,
                    data=json_documents,
                    headers=https_headers
                )
                self.stdout.write("Indexed courses: " + str(start) + " - " + str(start + count) + "   status_code=" + str(response.status_code))

            except Exception as error:
                raise CommandError("Elastic indexing error: " + str(error))


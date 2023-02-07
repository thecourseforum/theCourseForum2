# pylint: disable=line-too-long
"""
TODO: write
"""


import json

from django.core.management.base import BaseCommand
from tcf_website.models import Course


class Command(BaseCommand):
    """TODO: write"""

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with open('tcf_website/management/commands/semester_data/all-data.json', 'r', encoding='utf-8') as file:
            data = json.loads(file.read())
        print("ligma cope cope ligma ligma ligma cope")
        courses_to_update = []
        # Note: every single class in data has precisely 1 "offering"
        for subject, subject_data in data.items():
            if subject == 'CS':
                for course_id, course_data in subject_data['courses'].items():
                    course, created = Course.objects.get

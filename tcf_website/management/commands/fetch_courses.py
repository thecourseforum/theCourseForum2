# pylint: disable=line-too-long
"""
TODO: write
"""

import json
import requests

from django.core.management.base import BaseCommand
from tcf_website.models import Subject

SIS_ENDPOINT = 'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_COURSE_CATALOG.FieldFormula' \
               '.IScript_'
ALL_SUBJECTS_ENDPOINT = f'{SIS_ENDPOINT}CatalogSubjects?institution=UVA01&x_acad_career=UGRD'
# Currently hardcoded to only find undergrad classes
# Use as f'{SUBJECT_ENDPOINT}&subject={SUBJECT}'
SUBJECT_ENDPOINT = f'{SIS_ENDPOINT}SubjectCourses?institution=UVA01&x_acad_career=UGRD'
# Intercepted HTTP request from SIS used extra flags:
# &crse_offer_nbr=1&use_catalog_print=Y
# but idk what they do
# Course ID should match what the subject endpoint provides, *not* Lou's
COURSE_ENDPOINT = f'{SIS_ENDPOINT}CatalogCourseDetails?institution=UVA01&effdt=2022-11-18&x_acad_career=UGRD'


class Command(BaseCommand):
    """TODO: write"""

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        req = requests.get(ALL_SUBJECTS_ENDPOINT, timeout=5)
        subjects = req.json()['subjects']
        data = {}
        for subject in subjects:
            subject_code = subject['subject']
            data[subject_code] = {'description': subject['descr'], 'courses': {}}
            req = requests.get(f'{SUBJECT_ENDPOINT}&subject={subject_code}', timeout=5)
            courses = req.json()['courses']
            for course in courses:
                print(course)
                course_id = course["crse_id"]
                req = requests.get(f'{COURSE_ENDPOINT}&course_id={course_id}', timeout=5)
                course_details = req.json()['course_details']
                data[subject_code]['courses'][course_id] = course_details
        with open('tcf_website/management/commands/all-data.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data, indent=2))


# Helper functions used for data exploration

def subject_discrepancies(subjects):
    """Checks discrepancies list of subjects between SIS data and our database"""
    print("CHECK SUBJECT NAMES")
    names = [x['descr'] for x in subjects]
    known_names = Subject.objects.all().values_list('name', flat=True)

    print('in SIS but not DB:')
    print(list(set(names) - set(known_names)))

    print('in DB but not SIS')
    print(list(set(known_names) - set(names)))
    print('———————————————————————————')
    print("CHECK SUBJECT CODES")
    names = [x['subject'] for x in subjects]
    known_names = Subject.objects.all().values_list('mnemonic', flat=True)

    print('in SIS but not DB:')
    print(list(set(names) - set(known_names)))

    print('in DB but not SIS')
    print(list(set(known_names) - set(names)))


def subject_name_discrepancies(subjects):
    """
    Checks discrepancies in subject names given matching codes.
    For example, RELB being "Religion-Buddhism" vs. just "Buddhism"
    """
    existing_subjects = Subject.objects.all().values_list('mnemonic', flat=True)
    for subject in subjects:
        mnemonic = subject['subject']
        if mnemonic in existing_subjects:
            if Subject.objects.get(mnemonic=mnemonic).name != subject['descr']:
                print(mnemonic)
                print('old:', Subject.objects.get(mnemonic=mnemonic).name)
                print('new:', subject['descr'])
                print('--------------------------------')

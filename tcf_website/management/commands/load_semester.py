# pylint: disable=line-too-long
"""
TODO: write
"""

from django.core.management.base import BaseCommand

import requests


class Command(BaseCommand):
    """TODO: write"""

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        req = requests.get(
            'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_COURSE_CATALOG.FieldFormula.IScript_CatalogSubjects?institution=UVA01&x_acad_career=UGRD',
            timeout=5)
        subjects = req.json()
        print(subjects['subjects'])

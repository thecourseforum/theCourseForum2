from time import sleep
import os
import json

from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from tcf_website.models import *

from .grade_data.fetch_data import download_grade_data

'''
TODO:
    - DONE: port schools
    - DONE: port departments
    - DONE: port subdepartments
    - DONE: port semester
    - port sections
    - DONE*: port courses
    - DONE*: port instructors --- need to figure out how that will work!
    - port students --- need to figure out how that will work!
    - port reviews
    - port votes
    - check that all courses departments + subdepartments currently
        viewable on the website are in the migrated database

Done* denotes that it could be improved.

'''
import traceback


class Command(BaseCommand):
    help = 'Imports data from legacy database into default database'

    def migrate(
            self,
            legacy_class,
            new_class,
            field_map,
            unique_fields,
            reverse=False,
            after_func=None):

        def not_yet_created(obj):

            def get_or_call(old_field):
                if callable(old_field):
                    try:
                        return old_field(obj)
                    except BaseException:
                        return False
                return getattr(obj, old_field)

            return len(new_class.objects.filter(**{f"{new_field}__exact": get_or_call(
                old_field) for new_field, old_field in unique_fields.items()})) == 0

        if not reverse:
            objects = legacy_class.objects.using('legacy').all()
        else:
            objects = legacy_class.objects.using(
                'legacy').all().order_by('-pk')

        for obj in objects:
            if not_yet_created(obj):
                try:
                    new_obj = new_class()
                    for new_field_name, value_func in field_map.items():
                        old_val = value_func(obj)
                        if old_val:
                            setattr(new_obj, new_field_name, value_func(obj))
                    new_obj.save()
                    print(f"Created {new_obj}")

                    if after_func and callable(after_func):
                        after_func(obj, new_obj)

                except Exception as e:
                    print(f"Error migrating {type(obj).__name__} {obj}:")
                    print(e)
                    traceback.print_exc()

    def handle(self, *args, **options):

        download_grade_data()  # download all

        courses = Course.objects.filter(semester_last_taught__year__gte=2015)

        path = 'tcf_website/management/commands/grade_data/json'
        already_fetched = set(os.listdir(path))

        for c in tqdm(courses, total=courses.count()):
            course = f"{c.subdepartment.mnemonic}{c.number}"

            if f'{course}.json' in already_fetched:
                continue

            download_grade_data(course, path)

            # sleep(random.uniform(0.5, 1.0))

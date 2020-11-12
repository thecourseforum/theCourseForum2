from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from tcf_website.legacy_models import *
from tcf_website.models import *

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
                    print(f"Created {new_obj}".encode('utf-8'))

                    if after_func and callable(after_func):
                        after_func(obj, new_obj)

                except Exception as e:
                    print(
                        f"Error migrating {type(obj).__name__} {obj}:".encode('utf-8'))
                    print(e)
                    traceback.print_exc()

    def handle(self, *args, **options):

        self.schools = Schools.objects.using('legacy').all()
        self.departments = Departments.objects.using('legacy').all()
        self.subdepartments = Subdepartments.objects.using('legacy').all()
        self.courses = Courses.objects.using('legacy').all()
        self.sections = Sections.objects.using('legacy').all()
        self.professors = Professors.objects.using('legacy').all()
        self.users = Users.objects.using('legacy').all()
        self.students = Students.objects.using('legacy').all()
        self.reviews = Reviews.objects.using('legacy').all()
        self.votes = Votes.objects.using('legacy').all()
        self.semesters = Semesters.objects.using('legacy').all()

        UNKNOWN_SCHOOL, _ = School.objects.get_or_create(name='UNKNOWN')
        UNKNOWN_DEPT, _ = Department.objects.get_or_create(
            name='UNKNOWN', school=UNKNOWN_SCHOOL)

        self.migrate(
            Schools,
            School,
            {
                'name': lambda school: school.name
            },
            {'name': 'name'},
        )

        def get_school(old_dept):
            try:
                return School.objects.get(name=old_dept.school.name)
            except BaseException:
                return UNKNOWN_SCHOOL

        self.migrate(
            Departments,
            Department,
            {
                'name': lambda old: old.name,
                'school': lambda old: get_school(old)
            },
            {'name': 'name'},
        )

        def get_department(old_subdepartment):
            with connections['legacy'].cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM departments_subdepartments WHERE subdepartment_id = %s", [
                        old_subdepartment.id])
                row = cursor.fetchone()
                try:
                    old_department = self.departments.get(pk=row[0])
                    return Department.objects.get(name=old_department.name)
                except BaseException as e:
                    print(e)
                    return UNKNOWN_DEPT

        # TODO: Create new subdepartments (e.g. INST and AIRS) and link
        # courses to them
        self.migrate(
            Subdepartments,
            Subdepartment,
            {
                'name': lambda old: old.name,
                'mnemonic': lambda old: old.mnemonic,
                'department': lambda old: get_department(old)
            },
            {'mnemonic': 'mnemonic'},
        )

        # TODO: better collection of instructor emails? lous list?
        # TODO: better handling of name collisions?

        def get_email(old):
            if not old.email_alias:
                return None
            return old.email_alias if '@' in old.email_alias else f"{old.email_alias}@virginia.edu"
        # Instructor.objects.all().delete()
        self.migrate(
            Professors,
            Instructor,
            {
                'first_name': lambda old: old.first_name,
                'last_name': lambda old: old.last_name,
                'email': lambda old: get_email(old),
                'website': lambda old: old.home_page,
            },
            {
                'last_name': 'last_name',
                'first_name': 'first_name',
                # 'email': lambda old: get_email(old),
            },
            # TODO: associate instructors with departments
            # after_func = lambda old, new: new.departments.add(Department.objects.get(name=old.department.name))
        )

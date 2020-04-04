from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from tcf_website.legacy_models import *
from tcf_website.models import *

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

    
    def migrate(self, legacy_class, new_class, field_map, unique_fields, reverse=False, after_func=None):

        def not_yet_created(obj):

            def get_or_call(old_field):
                if callable(old_field):
                    try:
                        return old_field(obj)
                    except:
                        return False
                return getattr(obj, old_field)

            return len(new_class.objects.filter(**{
                f"{new_field}__exact": get_or_call(old_field) for new_field, old_field in unique_fields.items()}
            )) == 0

        if not reverse:
            objects = legacy_class.objects.using('legacy').all()
        else:
            objects = legacy_class.objects.using('legacy').all().order_by('-pk')

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
        
        '''
        self.migrate(
            Schools,
            School,
            {
                'name': lambda school: school.name
            },
            {'name': 'name'},
        )

        self.migrate(
            Departments,
            Department,
            {
                'name': lambda old: old.name,
                'school': lambda old: School.objects.get(name=old.school.name)
            },
            {'name': 'name'},
        )

        def get_department_name(old_subdepartment):
            with connections['legacy'].cursor() as cursor:
                cursor.execute("SELECT * FROM departments_subdepartments WHERE subdepartment_id = %s", [old_subdepartment.id])
                row = cursor.fetchone()
                return self.departments.get(pk=row[0]).name

        # TODO: Create new subdepartments (e.g. INST and AIRS) and link
        # courses to them
        self.migrate(
            Subdepartments,
            Subdepartment,
            {
                'name': lambda old: old.name,
                'mnemonic': lambda old: old.mnemonic,
                'department': lambda old: Department.objects.get(name=get_department_name(old))
            },
            {'mnemonic': 'mnemonic'},
        )

        self.migrate(
            Semesters,
            Semester,
            {
                'number': lambda old: old.number,
                'year': lambda old: old.year,
                'season': lambda old: old.season.upper(),
                
            },
            {'number': 'number'},
        )

        
        # Course.objects.all().delete()
        self.migrate(
            Courses,
            Course,
            {
                'title': lambda old: old.title,
                'description': lambda old: old.description,
                'number': lambda old: old.course_number,
                'subdepartment': lambda old: Subdepartment.objects.get(name=old.subdepartment.name),
                'semester_last_taught': lambda old: Semester.objects.get(number=old.last_taught_semester.number),
                
            },
            {
                'subdepartment__name': lambda old: old.subdepartment.name,
                'number': 'course_number',
            },
            reverse=True
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

        '''

        def get_section_instructor(old_sec):
            with connections['legacy'].cursor() as cursor:
                cursor.execute("SELECT * FROM section_professors WHERE section_id = %s", [old_sec.id])
                row = cursor.fetchone()
                prof = self.professors.get(pk=row[0])
                print(f"found instructor {prof} for {old_sec}")
                return {
                    'first_name': prof.first_name,
                    'last_name': prof.last_name
                    }
        # Section.objects.all().delete()
        # self.migrate(
        #     Sections,
        #     Section,
        #     {
        #         'sis_section_number': lambda old: old.sis_class_number,
        #         'semester': lambda old: Semester.objects.get(number=old.semester.number),
        #         'course': lambda old: Course.objects.get(number=old.course.course_number, subdepartment=Subdepartment.objects.get(name=old.course.subdepartment.name)),
                
        #     },
        #     {
        #         'course__subdepartment__name': lambda old: old.subdepartment.name,
        #         'course__number': lambda old: old.course.course_number,
        #     },
        #     after_func = lambda old, new: new.instructors.add(
        #         Instructor.objects.get(**get_section_instructor(old)))
        # )
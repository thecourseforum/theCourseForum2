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
    - port courses
    - port instructors --- need to figure out how that will work!
    - port students --- need to figure out how that will work!
    - port reviews
    - port votes


'''





class Command(BaseCommand):
    help = 'Imports data from legacy database into default database'

    
    def migrate(self, legacy_class, new_class, field_map, unique_fields, reverse=False):

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
                # new_obj = new_class(**{
                #     new_field_name: value_func(obj) for new_field_name, value_func in field_map.items()
                # })
                # new_obj.save()
                try:
                    new_obj = new_class()
                    for new_field_name, value_func in field_map.items():
                        old_val = value_func(obj)
                        if old_val:
                            setattr(new_obj, new_field_name, value_func(obj))
                    new_obj.save()
                    print(f"Created {new_obj}")
                except Exception as e:
                    print(f"Error migrating {type(obj).__name__} {obj}:")
                    print(e)


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

        # self.migrate(
        #     Courses,
        #     Course,
        #     {
        #         'title': lambda old: old.title,
        #         'description': lambda old: old.description,
        #         'number': lambda old: old.course_number,

        #     },
        #     'mnemonic',
        # )
        
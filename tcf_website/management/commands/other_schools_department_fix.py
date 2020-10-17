from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import *


class Command(BaseCommand):
    help = 'Promotes subdepartments in \'Other Schools at the University of Virginia\' to departments'

    def handle(self, *args, **options):
        excluded = [
            "College of Arts & Sciences",
            "School of Engineering & Applied Science",
            "UNKNOWN"]
        # dash = '-'*185
        # print(dash)
        # print('{:<70s}{:<70s}{:<70s}'.format('Subdepartment', 'Department', 'School'))
        # print(dash)

        # Go through all schools that are not in the list of excluded
        for school in School.objects.exclude(name__in=excluded):
            # Go through all departments
            for department in school.department_set.all():
                # Go through all subdepartments
                for subdepartment in department.subdepartment_set.all():
                    #             print('{:<70s}{:<70s}{:<70s}'.format(subdepartment.name, department.name, school.name))
                    #     print(dash)   
                    # Promote the subdepartment to a department
                    new_department = Department(
                        name=subdepartment.name,
                        school=school
                    )
                    # Reassign relation
                    subdepartment.department = new_department
                    # Save everything
                    new_department.save()
                    subdepartment.save()
                # Delete old department
                department.delete()

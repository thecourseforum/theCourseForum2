from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import *


class Command(BaseCommand):

    help = 'Promotes subdepartments in \'Other Schools at the University of Virginia\' to departments'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):

        self.verbose = options['verbose']

        # Take Other Schools at UVA and promote all subdepartments into departments
        # Excluded schoosl not to split up
        excluded = [
            "College of Arts & Sciences",
            "School of Engineering & Applied Science",
            "UNKNOWN"]

        if self.verbose:
            dash = '-'*185
            print(dash)
            print('{:<70s}{:<70s}{:<70s}'.format('Subdepartment', 'Department', 'School'))
            print(dash)

        # Go through all schools that are not in the list of excluded
        for school in School.objects.exclude(name__in=excluded):
            # Go through all departments
            for department in school.department_set.all():
                # Go through all subdepartments
                for subdepartment in department.subdepartment_set.all():
                    if self.verbose:
                        print('{:<70s}{:<70s}{:<70s}'.format(subdepartment.name, department.name, school.name))
                        print(dash)   
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

        ## Moving Computer Science from A&S to School of Engineering
        # Get the School of Engineering and Computer Science department instances
        E_School = School.objects.get(name='School of Engineering & Applied Science')
        Comp_Sci = Department.objects.get(name="Computer Science")
        # Assign school
        Comp_Sci.school = E_School
        # Save changes
        Comp_Sci.save()
        
        if self.verbose:
            print('Moved Computer Science to School of Engineering')


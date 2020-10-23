from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import *


class Command(BaseCommand):

    # Run this coomand using `sudo docker exec -it tcf_django python3 manage.py other_schools_department_fix`
    # Optional flag --verbose can be set to show output of the script
    # Must be run in a separate terminal after already running docker-compose up
    # May have to restart the docker container for database changes to be visible on the site
    # Visually check that CS department has been moved to E School and that
    # other schools have been split up.

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
        # Excluded schools not to split up
        excluded = [
            "College of Arts & Sciences",
            "School of Engineering & Applied Science",
            "UNKNOWN"]

        if self.verbose:
            dash = '-' * 185
            print(dash)
            print(
                '{:<70s}{:<70s}{:<70s}'.format(
                    'Subdepartment',
                    'Department',
                    'School'))
            print(dash)

        # Go through all schools that are not in the list of excluded
        for school in School.objects.exclude(name__in=excluded):
            # Go through all departments
            for department in school.department_set.all():
                # Go through all subdepartments
                for subdepartment in department.subdepartment_set.all():
                    if self.verbose:
                        print(
                            '{:<70s}{:<70s}{:<70s}'.format(
                                subdepartment.name,
                                department.name,
                                school.name))
                        print(dash)
                    # Promote the subdepartment to a department
                    new_department = Department(
                        name=subdepartment.name,
                        school=school,
                        description=subdepartment.description
                    )
                    # Reassign relation
                    subdepartment.department = new_department
                    # Save everything
                    new_department.save()
                    subdepartment.save()
                # Delete old department
                department.delete()

        # Moving Computer Science from A&S to School of Engineering
        # Get the School of Engineering and Computer Science department
        # instances
        e_school = School.objects.get(
            name='School of Engineering & Applied Science')
        comp_sci = Department.objects.get(name="Computer Science")
        # Assign school
        comp_sci.school = e_school
        # Save changes
        comp_sci.save()

        if self.verbose:
            print('Moved Computer Science to School of Engineering')

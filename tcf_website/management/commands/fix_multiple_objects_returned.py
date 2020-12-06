from functools import reduce
from operator import or_

from django.core.management.base import BaseCommand
from django.db.models import Case, Count, F, FloatField, Q, Sum, Value, When

from tcf_website.models import CourseInstructorGrade


class Command(BaseCommand):
    """This fixes existing `MultipleObjectsReturned` errors"""

    help = 'Fix `MultipleObjectsReturned` errors that were caused by inconsistent email data'

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']

        # Number of cases we want to fix
        qs = CourseInstructorGrade.objects\
            .exclude(course=None)\
            .values('course', 'first_name', 'last_name')\
            .annotate(num=Count('id'))\
            .filter(num__gt=1)
        if self.verbosity > 0:
            print(qs.count())

        qs_without_num = qs.values('course', 'first_name', 'last_name')
        total = CourseInstructorGrade.objects\
            .filter(reduce(or_, [Q(**a) for a in qs_without_num]))\
            .order_by('first_name', 'last_name', 'subdepartment', 'number')
        without_email = total.filter(email='')

        # Fix the weird case with two different emails for the same professor
        to_fix = list(CourseInstructorGrade.objects.filter(
            email='lr4zs@virginia.edu',
        ))
        for obj in to_fix:
            obj.email = ''
        CourseInstructorGrade.objects.bulk_update(to_fix, ['email'])

        # Now everything should have been fixed.
        if self.verbosity > 0:
            print(without_email.count())

        for a in qs_without_num:
            instructors = list(
                CourseInstructorGrade.objects.filter(**a).order_by('email')
            )
            # The second one has the email, and the first one doesn't
            instructors[0].email = instructors[1].email
            instructors[0].save()

        # Now combine the duplicate instances
        fields_to_group_by = [
            'subdepartment', 'number', 'first_name', 'middle_name',
            'last_name', 'email', 'course_id', 'instructor_id',
        ]
        fields_to_sum = [
            'a_plus', 'a', 'a_minus', 'b_plus', 'b', 'b_minus', 'c_plus', 'c',
            'c_minus', 'd_plus', 'd', 'd_minus', 'f', 'ot', 'drop', 'withdraw',
            'total_enrolled',
        ]
        fields_to_compute = ['average']
        fields_all = fields_to_group_by + fields_to_sum + fields_to_compute

        instances_to_fix = total
        combined = list(
            instances_to_fix
            .values(*fields_to_group_by)
            .annotate(
                **{field: Sum(field) for field in fields_to_sum},
                actual_enrolled=(F('total_enrolled') -
                                 F('ot') - F('drop') - F('withdraw')),
                average=Case(
                    When(
                        actual_enrolled__gt=0,
                        then=((
                            F('a_plus') * 4.0 + F('a') * 4.0 +
                            F('a_minus') * 3.7 + F('b_plus') * 3.3 +
                            F('b') * 3.0 + F('b_minus') * 2.7 +
                            F('c_plus') * 2.3 + F('c') * 2.0 +
                            F('d_plus') * 1.3 + F('d') * 1.0 + F('f') * 0.0
                        ) / F('actual_enrolled'))
                    ),
                    default=Value('0'),
                    output_field=FloatField()
                )
            ).values(*fields_all)  # to exclude actual_enrolled
        )
        # Drop problematic instances
        instances_to_fix.delete()
        # Create fixed instances
        objects_created = CourseInstructorGrade.objects.bulk_create(
            [CourseInstructorGrade(**x) for x in combined])
        if self.verbosity > 0:
            print(len(objects_created))

        # Check the number of `MultipleObjectsReturned` error again
        assert CourseInstructorGrade.objects\
            .exclude(course=None)\
            .exclude(instructor=None)\
            .values('course', 'instructor')\
            .annotate(num=Count('id'))\
            .filter(num__gt=1).count() == 0, \
            'Multiple `CourseInstructorGrade`s for (course, instructor) pair?'

        assert CourseInstructorGrade.objects\
            .exclude(course=None)\
            .exclude(instructor=None)\
            .values('course', 'first_name', 'last_name')\
            .annotate(num=Count('id'))\
            .filter(num__gt=1).count() == 0, \
            'Multiple `CourseInstructorGrade`s for professors with same name'

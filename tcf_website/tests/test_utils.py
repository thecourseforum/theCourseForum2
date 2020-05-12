# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
# pylint: disable=duplicate-code
"""Common testing utilities."""

from ..models import *


def setup(obj):
    """Load some example data"""

    obj.school = School.objects.create(name="School of Hard Knocks")
    obj.department = Department.objects.create(
        name="Computer Science",
        school=obj.school
    )
    obj.subdepartment = Subdepartment.objects.create(
        name="Computer Science",
        mnemonic="CS",
        department=obj.department
    )
    obj.semester = Semester.objects.create(
        year=2020,
        season='FALL',
        number=1208
    )
    obj.course = Course.objects.create(
        title="Software Testing",
        description="Super advanced and smart tests.",
        number=420,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.semester
    )

    obj.user1 = User.objects.create(
        username="tcf2yay",
        email="tcf2yay@virginia.edu",
        computing_id="tcf2yay",
    )
    obj.user2 = User.objects.create(
        username="tcf3yay",
        email="tcf3yay@virginia.edu",
        computing_id="tcf3yay",
    )

    obj.instructor = Instructor.objects.create(
        last_name="Jefferson",
        first_name="Tom"
    )

    obj.review1 = Review.objects.create(
        user=obj.user1,
        course=obj.course,
        semester=obj.semester,
        instructor=obj.instructor,
        text="Class sucks.",
        instructor_rating=1,
        difficulty=5,
        recommendability=1,
        hours_per_week=168,
    )

    obj.review2 = Review.objects.create(
        user=obj.user2,
        course=obj.course,
        semester=obj.semester,
        instructor=obj.instructor,
        text="Class rocks.",
        instructor_rating=5,
        difficulty=1,
        recommendability=5,
        hours_per_week=3,
    )

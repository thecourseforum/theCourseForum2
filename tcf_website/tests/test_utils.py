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
    obj.past_semester = Semester.objects.create(
        year=2010,
        season='FALL',
        number=1108
    )
    obj.course = Course.objects.create(
        title="Software Testing",
        description="Super advanced and smart tests.",
        number=420,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.semester
    )
    obj.course2 = Course.objects.create(
        title="Algorithms",
        description="Super hard algorithms.",
        number=421,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.semester
    )
    obj.course3 = Course.objects.create(
        title="Program & Data Structures",
        description="Many complicated data structures.",
        number=422,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.past_semester
    )
    obj.course4 = Course.objects.create(
        title="Operating Systems",
        description="Very low-level stuff.",
        number=423,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.past_semester
    )
    obj.course5 = Course.objects.create(
        title="Introduction to Programming",
        description="Intro.",
        number=424,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.past_semester
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
        enjoyability=1,
        hours_per_week=80,
        amount_group=20,
        amount_reading=20,
        amount_writing=20,
        amount_homework=20
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
        enjoyability=4,
        hours_per_week=3,
        amount_group=1,
        amount_reading=2,
        amount_writing=0,
        amount_homework=0
    )

    obj.review3 = Review.objects.create(
        user=obj.user1,
        course=obj.course2,
        semester=obj.semester,
        instructor=obj.instructor,
        text="Awesome.",
        instructor_rating=4,
        difficulty=4,
        recommendability=5,
        enjoyability=4,
        hours_per_week=6,
        amount_group=1,
        amount_reading=2,
        amount_writing=3,
        amount_homework=0
    )

    obj.review4 = Review.objects.create(
        user=obj.user2,
        course=obj.course2,
        semester=obj.semester,
        instructor=obj.instructor,
        text="Brilliant.",
        instructor_rating=5,
        difficulty=2,
        recommendability=5,
        enjoyability=4,
        hours_per_week=5,
        amount_group=1,
        amount_reading=2,
        amount_writing=0,
        amount_homework=2
    )

    obj.review5 = Review.objects.create(
        user=obj.user2,
        course=obj.course3,
        semester=obj.semester,
        instructor=obj.instructor,
        text="Cool.",
        instructor_rating=3,
        difficulty=3,
        recommendability=3,
        enjoyability=4,
        hours_per_week=2,
        amount_group=0,
        amount_reading=2,
        amount_writing=0,
        amount_homework=0
    )

    obj.review6 = Review.objects.create(
        user=obj.user2,
        course=obj.course4,
        semester=obj.semester,
        instructor=obj.instructor,
        text="Damn easy.",
        instructor_rating=2,
        difficulty=1,
        recommendability=1,
        enjoyability=4,
        hours_per_week=4,
        amount_group=1,
        amount_reading=2,
        amount_writing=1,
        amount_homework=0
    )

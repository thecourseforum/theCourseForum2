# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
# pylint: disable=duplicate-code
"""Common testing utilities."""

import logging

from ..models import *


def setup(obj):
    """Load some example data"""

    obj.school = School.objects.create(name="School of Hard Knocks")
    obj.department = Department.objects.create(
        name="Computer Science", school=obj.school
    )
    obj.subdepartment = Subdepartment.objects.create(
        name="Computer Science", mnemonic="CS", department=obj.department
    )
    obj.semester = Semester.objects.create(
        year=2020, season="FALL", number=1208
    )
    obj.past_semester = Semester.objects.create(
        year=2010, season="FALL", number=1108
    )
    obj.incomplete_semester = Semester.objects.create(year=2019, number=1198)

    obj.course = Course.objects.create(
        title="Software Testing",
        description="Super advanced and smart tests.",
        number=1420,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.semester,
    )
    obj.course2 = Course.objects.create(
        title="Algorithms",
        description="Super hard algorithms.",
        number=1421,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.semester,
    )
    obj.course3 = Course.objects.create(
        title="Program & Data Structures",
        description="Many complicated data structures.",
        number=1422,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.past_semester,
    )
    obj.course4 = Course.objects.create(
        title="Operating Systems",
        description="Very low-level stuff.",
        number=1423,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.past_semester,
    )
    obj.course5 = Course.objects.create(
        title="Introduction to Programming",
        description="Intro.",
        number=1424,
        subdepartment=obj.subdepartment,
        semester_last_taught=obj.past_semester,
    )

    obj.user1 = User.objects.create(
        username="tcf2yay",
        email="tcf2yay@virginia.edu",
        computing_id="tcf2yay",
        first_name="Taylor",
        last_name="Comb",
        graduation_year=2023,
    )
    obj.user2 = User.objects.create(
        username="tcf3yay", computing_id="tcf3yay", last_name="NoFirstName"
    )
    obj.user3 = User.objects.create(
        username="bnf89798",
        computing_id="bnf89798",
        first_name="Bam",
        last_name="Friedman",
    )
    obj.user4 = User.objects.create(
        username="kik878",
        computing_id="kik878",
        first_name="Kjell",
        last_name="Kool",
    )

    obj.instructor = Instructor.objects.create(
        last_name="Jefferson", first_name="Tom", email="tjt3rea@virginia.edu"
    )

    obj.section_course = Section.objects.create(
        course=obj.course, semester=obj.semester, sis_section_number=312312
    )

    obj.section_course.instructors.set(
        Instructor.objects.filter(pk=obj.instructor.pk)
    )

    obj.section_course2 = Section.objects.create(
        course=obj.course2, semester=obj.semester, sis_section_number=31232
    )
    obj.section_course2.instructors.set(
        Instructor.objects.filter(pk=obj.instructor.pk)
    )

    obj.instructor_grade = CourseInstructorGrade.objects.create(
        instructor=obj.instructor,
        course=obj.course,
        average=3.8,
    )

    obj.instructor_grade2 = CourseInstructorGrade.objects.create(
        instructor=obj.instructor, course=obj.course, average=3.2
    )

    obj.instructor_grade3 = CourseInstructorGrade.objects.create(
        instructor=obj.instructor, course=obj.course2, average=3.9
    )

    obj.instructor2 = Instructor.objects.create(
        first_name="No", last_name="Email"
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
        amount_homework=20,
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
        amount_homework=0,
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
        amount_homework=0,
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
        amount_homework=2,
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
        amount_homework=0,
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
        amount_homework=0,
    )

    obj.course_grade = CourseGrade.objects.create(
        course=obj.course, average=2.9
    )

    obj.upvote_review1 = Vote.objects.create(
        value=1, user=obj.user1, review=obj.review1
    )

    obj.upvote_review1_2 = Vote.objects.create(
        value=1, user=obj.user2, review=obj.review1
    )
    obj.downvote_review1 = Vote.objects.create(
        value=-1, user=obj.user3, review=obj.review1
    )


def create_new_semester(self, year):
    """Helper method to modify current semester"""
    self.semester = Semester.objects.create(
        year=year, season="FALL", number=f"1{year % 100}8"
    )


def suppress_request_warnings(original_function):
    """
    Suppress unnecessary request error messages in tests.

    Source: https://stackoverflow.com/a/46079090
    """

    def new_function(*args, **kwargs):
        # raise logging level to ERROR
        logger = logging.getLogger("django.request")
        previous_logging_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)
        # trigger original function that would throw warning
        original_function(*args, **kwargs)
        # lower logging level back to previous
        logger.setLevel(previous_logging_level)

    return new_function

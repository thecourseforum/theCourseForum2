# pylint: disable=line-too-long

"""TCF Models module."""

# See
# https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .models import (
    Answer,
    Course,
    CourseEnrollment,
    CourseGrade,
    CourseInstructorGrade,
    Department,
    Discipline,
    Instructor,
    Question,
    Review,
    School,
    Section,
    SectionTime,
    SectionEnrollment,
    Semester,
    Subdepartment,
    User,
    Vote,
)

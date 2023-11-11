# pylint: disable=line-too-long

"""TCF Models module."""

# See
# https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .models import (
    Answer,
    Course,
    CourseGrade,
    CourseInstructorGrade,
    Department,
    Instructor,
    Question,
    Review,
    School,
    Section,
    Semester,
    Subdepartment,
    User,
    Vote,
)

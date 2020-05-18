# pylint disable=bad-continuation

"""Views for Browse, department, and course/course instructor pages."""

from django.shortcuts import render
from django.urls import reverse

from ..models import School, Department, Course, Semester, Instructor, Review


def browse(request):
    """View for browse page."""
    clas = School.objects.get(name="College of Arts & Sciences")
    seas = School.objects.get(name="School of Engineering & Applied Science")

    # Other schools besides CLAS and SEAS.
    # other_school_pks = School.objects.exclude(
    #     pk__in=[
    #         clas.pk,
    #         seas.pk]).values_list(
    #             'department',
    #             flat=True)
    # other_schools_depts = Department.objects.filter(pk__in=other_school_pks)
    other_schools = School.objects.exclude(pk__in=[clas.pk,seas.pk])

    return render(request, 'browse/browse.html', {
        'CLAS': clas,
        'SEAS': seas,
        'other_schools': other_schools
    })


def department(request, dept_id):
    """View for department page."""

    # Prefetch related subdepartments and courses to improve performance.
    # department.html loops through related subdepartments and courses.
    # See:
    # https://docs.djangoproject.com/en/3.0/ref/models/querysets/#django.db.models.query.QuerySet.prefetch_related
    dept = Department.objects.prefetch_related(
        'subdepartment_set',
        'subdepartment_set__course_set').get(
            pk=dept_id)

    # Get the most recent semester
    latest_semester = Semester.latest()

    # Navigation breadcrimbs
    breadcrumbs = [
        (dept.school.name, reverse('browse'), False),
        (dept.name, None, True)
    ]

    return render(request, 'department/department.html',
                  {
                      'department': dept,
                      'latest_semester': latest_semester,
                      'breadcrumbs': breadcrumbs
                  })


def course_view(request, course_id):
    """View for course page."""

    course = Course.objects.get(pk=course_id)
    latest_semester = Semester.latest()

    # Get instructors that have taught the course in the most recent
    # semester.
    recent_instructor_pks = course.section_set.filter(
        semester=latest_semester).values_list(
            'instructors', flat=True).distinct()
    recent_instructors = Instructor.objects.filter(
        pk__in=recent_instructor_pks)
    # Add ratings and difficulties
    for instr in recent_instructors:
        instr.rating = instr.average_rating_for_course(course)
        instr.difficulty = instr.average_difficulty_for_course(course)

    # Get instructors that haven't taught the course this semester.
    old_instructor_pks = course.section_set.exclude(
        semester=latest_semester).exclude(
            instructors__pk__in=recent_instructor_pks).values_list(
                'instructors',
                flat=True).distinct()
    old_instructors = Instructor.objects.filter(pk__in=old_instructor_pks)
    # Add ratings and difficulties
    for instr in old_instructors:
        instr.rating = instr.average_rating_for_course(course)
        instr.difficulty = instr.average_difficulty_for_course(course)

    dept = course.subdepartment.department

    # Navigation breadcrumbs
    breadcrumbs = [
        (dept.school.name, reverse('browse'), False),
        (dept.name, reverse('department', args=[dept.pk]), False),
        (course.code, None, True),
    ]

    return render(request, 'course/course.html',
                  {
                      'course': course,
                      'recent_instructors': recent_instructors,
                      'latest_semester': latest_semester,
                      'old_instructors': old_instructors,
                      'breadcrumbs': breadcrumbs
                  })


def course_instructor(request, course_id, instructor_id):
    """View for course instructor page."""

    course = Course.objects.get(pk=course_id)
    instructor = Instructor.objects.get(pk=instructor_id)

    # Filter out reviews with no text.
    reviews = Review.display_reviews(course, instructor, request.user)

    dept = course.subdepartment.department

    # Navigation breadcrumbs
    breadcrumbs = [
        (dept.school.name, reverse('browse'), False),
        (dept.name, reverse('department', args=[dept.pk]), False),
        (course.code, reverse('course', args=[course.pk]), False),
        (instructor.full_name, None, True)
    ]

    # Get average statistics.
    rating = instructor.average_rating_for_course(course)
    difficulty = instructor.average_difficulty_for_course(course)
    hours = instructor.average_hours_for_course(course)

    return render(request, 'course/course_professor.html',
                  {
                      'course': course,
                      'instructor': instructor,
                      'reviews': reviews,
                      'breadcrumbs': breadcrumbs,
                      'rating': rating,
                      'difficulty': difficulty,
                      'hours': hours,
                  })

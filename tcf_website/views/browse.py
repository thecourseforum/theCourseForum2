# pylint disable=bad-continuation

"""Views for Browse, department, and course/course instructor pages."""
import json
from typing import Any, Dict, List

from django.db.models import Avg, CharField, F, Max, Q, Value
from django.db.models.functions import Concat
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from ..models import (
    School,
    Department,
    Course,
    Section,
    Semester,
    Instructor,
    Review,
    CourseInstructorGrade)


def browse(request):
    """View for browse page."""
    clas = School.objects.get(name="College of Arts & Sciences")
    seas = School.objects.get(name="School of Engineering & Applied Science")

    excluded_list = [clas.pk, seas.pk]
    # Get the Misc category so it can be appended at the end (if it exists)
    try:
        misc_school = School.objects.get(name="Miscellaneous")
        excluded_list.append(misc_school.pk)
    except ObjectDoesNotExist:
        misc_school = None

    # Other schools besides CLAS, SEAS, and Misc.
    other_schools = School.objects.exclude(pk__in=excluded_list)

    return render(request, 'browse/browse.html', {
        'CLAS': clas,
        'SEAS': seas,
        'other_schools': other_schools,
        'misc_school': misc_school
    })


def department(request, dept_id):
    """View for department page."""

    # Prefetch related subdepartments and courses to improve performance.
    # department.html loops through related subdepartments and courses.
    # See:
    # https://docs.djangoproject.com/en/3.0/ref/models/querysets/#django.db.models.query.QuerySet.prefetch_related
    dept = Department.objects.prefetch_related(
        'subdepartment_set').get(pk=dept_id)

    # Get the most recent semester
    latest_semester = Semester.latest()

    # Navigation breadcrimbs
    breadcrumbs = [
        (dept.school.name, reverse('browse'), False),
        (dept.name, None, True)
    ]

    return render(request, 'department/department.html',
                  {
                      'subdepartments': dept.subdepartment_set.all(),
                      'latest_semester': latest_semester,
                      'breadcrumbs': breadcrumbs
                  })


def course_view_legacy(request, course_id):
    """Legacy view for course page."""
    course = get_object_or_404(Course, pk=course_id)
    return redirect('course',
                    mnemonic=course.subdepartment.mnemonic,
                    course_number=course.number)


def course_view(request, mnemonic, course_number):
    """A new Course view that allows you to input mnemonic and number instead."""
    # Redirect if the mnemonic is not all uppercase
    if mnemonic != mnemonic.upper():
        return redirect('course',
                        mnemonic=mnemonic.upper(), course_number=course_number)
    course = get_object_or_404(
        Course, subdepartment__mnemonic=mnemonic.upper(), number=course_number)
    latest_semester = Semester.latest()
    instructors = Instructor.objects\
        .filter(section__course=course).distinct()\
        .annotate(
            gpa=Avg('courseinstructorgrade__average',
                    filter=Q(courseinstructorgrade__course=course)),
            difficulty=Avg('review__difficulty',
                           filter=Q(review__course=course)),
            rating=(
                Avg('review__instructor_rating', filter=Q(review__course=course)) +
                Avg('review__enjoyability', filter=Q(review__course=course)) +
                Avg('review__recommendability', filter=Q(review__course=course))
            ) / 3,
            semester_last_taught=Max('section__semester',
                                     filter=Q(section__course=course)),
        )
    taught_this_semester = Section.objects.filter(course=course, semester=latest_semester).exists()

    # Note: Wanted to use .annotate() but couldn't figure out a way
    # So created a dictionary on the fly to minimize database access
    semesters = {s.id: s for s in Semester.objects.all()}
    for instructor in instructors:
        instructor.semester_last_taught = semesters.get(
            instructor.semester_last_taught)

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
                      'instructors': instructors,
                      'latest_semester': latest_semester,
                      'breadcrumbs': breadcrumbs,
                      'taught_this_semester': taught_this_semester
                  })


def course_instructor(request, course_id, instructor_id):
    """View for course instructor page."""
    section_last_taught = Section.objects\
        .filter(course=course_id, instructors=instructor_id)\
        .order_by('semester')\
        .last()
    if section_last_taught is None:
        raise Http404
    course = section_last_taught.course
    instructor = section_last_taught.instructors.get(pk=instructor_id)

    # Filter out reviews with no text.
    reviews = Review.display_reviews(course_id, instructor_id, request.user)
    dept = course.subdepartment.department

    course_url = reverse('course',
                         args=[course.subdepartment.mnemonic, course.number])
    # Navigation breadcrumbs
    breadcrumbs = [
        (dept.school.name, reverse('browse'), False),
        (dept.name, reverse('department', args=[dept.pk]), False),
        (course.code, course_url, False),
        (instructor.full_name, None, True)
    ]

    data = Review.objects\
        .filter(course=course_id, instructor=instructor_id)\
        .aggregate(
            # rating stats
            average_rating=(
                Avg('instructor_rating') +
                Avg('enjoyability') +
                Avg('recommendability')
            ) / 3,
            average_instructor=Avg('instructor_rating'),
            average_fun=Avg('enjoyability'),
            average_recommendability=Avg('recommendability'),
            average_difficulty=Avg('difficulty'),
            # workload stats
            average_hours_per_week=Avg('hours_per_week'),
            average_amount_reading=Avg('amount_reading'),
            average_amount_writing=Avg('amount_writing'),
            average_amount_group=Avg('amount_group'),
            average_amount_homework=Avg('amount_homework'),
        )
    data = {key: safe_round(value) for key, value in data.items()}

    try:
        grades_data = CourseInstructorGrade.objects.get(
            instructor=instructor, course=course)
    except ObjectDoesNotExist:  # if no data found
        pass
    # NOTE: Don't catch MultipleObjectsReturned because we want to be notified
    else:  # Fill in the data found
        # grades stats
        data['average_gpa'] = round(grades_data.average, 2)
        fields = [
            'a_plus', 'a', 'a_minus',
            'b_plus', 'b', 'b_minus',
            'c_plus', 'c', 'c_minus',
            'no_credit', 'total_enrolled'
        ]
        for field in fields:
            data[field] = getattr(grades_data, field)

    return render(request, 'course/course_professor.html',
                  {
                      'course': course,
                      'course_id': course_id,
                      'instructor': instructor,
                      'semester_last_taught': section_last_taught.semester,
                      'reviews': reviews,
                      'breadcrumbs': breadcrumbs,
                      'data': json.dumps(data),
                  })


def instructor_view(request, instructor_id):
    """View for instructor page, showing all their courses taught."""
    instructor: Instructor = get_object_or_404(Instructor, pk=instructor_id)

    stats: Dict[str, float] = Instructor.objects\
        .filter(pk=instructor_id)\
        .prefetch_related('review_set')\
        .aggregate(
            avg_gpa=Avg('courseinstructorgrade__average'),
            avg_difficulty=Avg('review__difficulty'),
            avg_rating=(
                Avg('review__instructor_rating') +
                Avg('review__enjoyability') +
                Avg('review__recommendability')
            ) / 3)

    course_fields: List[str] = ['name', 'id', 'avg_rating', 'avg_difficulty',
                                'avg_gpa', 'last_taught']
    courses: List[Dict[str, Any]] = Course.objects\
        .filter(section__instructors=instructor, number__gte=1000)\
        .prefetch_related('review_set')\
        .annotate(
            subdepartment_name=F('subdepartment__name'),
            name=Concat(
                F('subdepartment__mnemonic'),
                Value(' '),
                F('number'),
                Value(' | '),
                F('title'),
                output_field=CharField(),
            ),
            avg_gpa=Avg('courseinstructorgrade__average',
                        filter=Q(courseinstructorgrade__instructor=instructor)),
            avg_difficulty=Avg('review__difficulty',
                               filter=Q(review__instructor=instructor)),
            avg_rating=(
                Avg('review__instructor_rating',
                    filter=Q(review__instructor=instructor)) +
                Avg('review__enjoyability',
                    filter=Q(review__instructor=instructor)) +
                Avg('review__recommendability',
                    filter=Q(review__instructor=instructor))
            ) / 3,
            last_taught=Concat(
                F('semester_last_taught__season'),
                Value(' '),
                F('semester_last_taught__year'),
                output_field=CharField(),
            ),
    ).values('subdepartment_name', *course_fields)\
        .order_by('subdepartment_name', 'name')

    grouped_courses: Dict[str, List[Dict[str, Any]]] = {}
    for course in courses:  # type: Dict[str, Any]
        course['avg_rating'] = safe_round(course['avg_rating'])
        course['avg_difficulty'] = safe_round(course['avg_difficulty'])
        course['avg_gpa'] = safe_round(course['avg_gpa'])
        course['last_taught'] = course['last_taught'].title()
        grouped_courses.setdefault(course['subdepartment_name'], []).append(course)

    context: Dict[str, Any] = {
        'instructor': instructor,
        **{key: safe_round(value) for key, value in stats.items()},
        'courses': grouped_courses,
    }
    return render(request, 'instructor/instructor.html', context)


def safe_round(num):
    """Helper function to reduce syntax repetitions for null checking rounding.

    Returns — if None is passed because that's what appears on the site when there's no data.
    """
    if num is not None:
        return round(num, 2)
    return '\u2014'

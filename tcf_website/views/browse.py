# pylint disable=bad-continuation

"""Views for Browse, department, and course/course instructor pages."""
import json

from django.db.models import Avg, Max, Q
from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from ..models import (
    School,
    Department,
    Subdepartment,
    Course,
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


def course_view(request, course_id):
    """View for course page."""

    course = Course.objects.get(pk=course_id)
    latest_semester = Semester.latest()
    instructors = Instructor.objects\
        .filter(section__course=course).distinct()\
        .annotate(
            gpa=Avg('courseinstructorgrade__average',
                    filter=Q(courseinstructorgrade__course=course)),
            difficulty=Avg('review__difficulty', filter=Q(review__course=course)),
            rating=(
                Avg('review__instructor_rating', filter=Q(review__course=course)) +
                Avg('review__enjoyability', filter=Q(review__course=course)) +
                Avg('review__recommendability', filter=Q(review__course=course))
            ) / 3,
            semester_last_taught=Max('section__semester',
                                     filter=Q(section__course=course)),
        )
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
                      'breadcrumbs': breadcrumbs
                  })


def course_instructor(request, course_id, instructor_id):
    """View for course instructor page."""

    course = Course.objects.get(pk=course_id)
    instructor = Instructor.objects\
        .filter(pk=instructor_id)\
        .annotate(
            semester_last_taught_id=Max('section__semester',
                                        filter=Q(section__course=course)),
        )
    instructor = instructor[0]
    # Note: Like view above, this is kinda a hacky way to get the last-taught
    # semester
    semester_last_taught = Semester.objects.get(
        pk=instructor.semester_last_taught_id)

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

    data = {
        # rating stats
        "average_rating": safe_round(instructor.average_rating_for_course(course)),
        "average_instructor": safe_round(instructor.average_instructor_rating_for_course(course)),
        "average_fun": safe_round(instructor.average_enjoyability_for_course(course)),
        "average_recommendability":
            safe_round(instructor.average_recommendability_for_course(course)),
        "average_difficulty": safe_round(instructor.average_difficulty_for_course(course)),
        # workload stats
        "average_hours_per_week": safe_round(instructor.average_hours_for_course(course)),
        "average_amount_reading": safe_round(instructor.average_reading_hours_for_course(course)),
        "average_amount_writing": safe_round(instructor.average_writing_hours_for_course(course)),
        "average_amount_group": safe_round(instructor.average_group_hours_for_course(course)),
        "average_amount_homework": safe_round(instructor.average_other_hours_for_course(course)),
    }

    try:
        grades_data = CourseInstructorGrade.objects.get(
            instructor=instructor, course=course)

        # grades stats
        data['average_gpa'] = round(grades_data.average, 2)
        data['a_plus'] = grades_data.a_plus
        data['a'] = grades_data.a
        data['a_minus'] = grades_data.a_minus
        data['b_plus'] = grades_data.b_plus
        data['b'] = grades_data.b
        data['b_minus'] = grades_data.b_minus
        data['c_plus'] = grades_data.c_plus
        data['c'] = grades_data.c
        data['c_minus'] = grades_data.c_minus
        data['d_plus'] = grades_data.d_plus
        data['d'] = grades_data.d
        data['d_minus'] = grades_data.d_minus
        data['f'] = grades_data.f
        data['withdraw'] = grades_data.withdraw
        data['drop'] = grades_data.drop

        fields = [
            'a_plus',
            'a',
            'a_minus',
            'b_plus',
            'b',
            'b_minus',
            'c',
            'c_minus',
            'd_plus',
            'd',
            'd_minus',
            'f',
            'withdraw',
            'drop']

        total = 0
        for field in fields:
            total += data[field]
        data['total_enrolled'] = total

    except ObjectDoesNotExist:  # if no data found
        pass

    data_json = json.dumps(data)

    return render(request, 'course/course_professor.html',
                  {
                      'course': course,
                      'course_id': course_id,
                      'instructor': instructor,
                      'semester_last_taught': semester_last_taught,
                      'reviews': reviews,
                      'breadcrumbs': breadcrumbs,
                      'data': data_json
                  })


def instructor_view(request, instructor_id):
    """View for instructor page, showing all their courses taught."""
    instructor = Instructor.objects.get(pk=instructor_id)

    avg_rating = safe_round(instructor.average_rating())
    avg_difficulty = safe_round(instructor.average_difficulty())
    avg_gpa = safe_round(instructor.average_gpa())

    courses = group_by_dept(instructor, instructor.get_courses())
    return render(
        request, 'instructor/instructor.html', {
            'instructor': instructor,
            'avg_rating': avg_rating,
            'avg_difficulty': avg_difficulty,
            'avg_gpa': avg_gpa,
            'courses': courses
        })


def group_by_dept(instructor, courses):
    """ Group instructor's courses by subdepartment.

        Returns a dictionary mapping subdepartment names to ids and
        lists of Course data.
    """
    subdept_ids = list(
        set(courses.values_list('subdepartment', flat=True)))

    # Contains IDs and names of all subdepartments for Instructor's Courses
    subdepts = sorted(
        list(
            map(
                lambda subdept_id: [
                    subdept_id,
                    Subdepartment.objects.get(
                        pk=subdept_id).name],
                subdept_ids)),
        key=lambda x: x[1])

    # Create dictionary corresponding dept to courses
    grouped_courses = {}
    for subdept in subdepts:
        grouped_courses[subdept[1]] = {
            "id": subdept[0],
            "courses": []
        }

    for course in courses:
        course_subdept = course.subdepartment.name
        course_data = {
            # autopep8 makes the formatting for this wack, sorry
            'name': str(course), 'id': course.id,
            'avg_rating': safe_round(
                Instructor.average_rating_for_course(
                    instructor, course)),
            'avg_difficulty': safe_round(
                Instructor.average_difficulty_for_course(
                    instructor, course)),
            'avg_gpa': safe_round(Instructor.average_gpa_for_course(instructor, course)),
            'last_taught': str(course.semester_last_taught)}
        grouped_courses[course_subdept]['courses'].append(course_data)

    return grouped_courses


def safe_round(num):
    """Helper function to reduce syntax repetitions for null checking rounding.

    Returns — if None is passed because that's what appears on the site when there's no data.
    """
    if num is not None:
        return round(num, 2)
    return '\u2014'

# pylint disable=bad-continuation

"""Views for Browse, department, and course/course instructor pages."""

from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from ..models import School, Department, Course, Semester, Instructor, Review, Subdepartment


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

    return render(request, 'course/course_professor.html',
                  {
                      'course': course,
                      'instructor': instructor,
                      'reviews': reviews,
                      'breadcrumbs': breadcrumbs,
                      'rating': rating,
                      'difficulty': difficulty,
                  })


def instructor_view(request, instructor_id):
    """View for instructor page, showing all their courses taught."""
    instructor = Instructor.objects.get(pk=instructor_id)

    avg_rating = safe_round(instructor.average_rating())
    avg_difficulty = safe_round(instructor.average_difficulty())

    courses = group_by_dept(instructor, instructor.get_courses())
    return render(
        request, 'instructor/instructor.html', {
            'instructor': instructor,
            'avg_rating': avg_rating,
            'avg_difficulty': avg_difficulty,
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
            'name': str(course), 'id': course.id, 'avg_rating': safe_round(
                Instructor.average_rating_for_course(
                    instructor, course)), 'avg_difficulty': safe_round(
                Instructor.average_difficulty_for_course(
                    instructor, course)), 'last_taught': str(
                course.semester_last_taught)}
        grouped_courses[course_subdept]['courses'].append(course_data)

    return grouped_courses


def safe_round(num):
    """Helper function to reduce syntax repetitions for null checking rounding.

    Returns — if None is passed because that's what appears on the site when there's no data.
    """
    if num is not None:
        return round(num, 2)
    return '\u2014'

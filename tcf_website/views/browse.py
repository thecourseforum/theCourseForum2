# pylint disable=bad-continuation

"""Views for Browse, department, and course/course instructor pages."""

from django.shortcuts import render
from django.urls import reverse

from ..models import School, Department, Course, Semester, Instructor, Review


def browse(request):
    """View for browse page."""
    clas = School.objects.get(name="College of Arts & Sciences")
    seas = School.objects.get(name="School of Engineering & Applied Science")

    other_dept_pks = School.objects.exclude(
        pk__in=[
            clas.pk,
            seas.pk]).values_list(
                'department',
                flat=True)

    other_depts = Department.objects.filter(pk__in=other_dept_pks)

    return render(request, 'browse/browse.html', {
        'CLAS': clas,
        'SEAS': seas,
        'other_depts': other_depts
    })


def department(request, dept_id):
    """View for department page."""
    dept = Department.objects.get(pk=dept_id)
    latest_semester = Semester.latest()

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

    recent_instructor_pks = course.section_set.filter(
        semester=latest_semester).values_list(
            'instructors', flat=True).distinct()
    recent_instructors = Instructor.objects.filter(
        pk__in=recent_instructor_pks)

    old_instructor_pks = course.section_set.exclude(
        semester=latest_semester).exclude(
            instructors__pk__in=recent_instructor_pks).values_list(
                'instructors',
                flat=True).distinct()
    old_instructors = Instructor.objects.filter(pk__in=old_instructor_pks)

    dept = course.subdepartment.department

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
    reviews = Review.objects.filter(
        instructor=instructor,
        course=course,
    ).exclude(text="").order_by("-created")

    dept = course.subdepartment.department

    breadcrumbs = [
        (dept.school.name, reverse('browse'), False),
        (dept.name, reverse('department', args=[dept.pk]), False),
        (course.code, reverse('course', args=[course.pk]), False),
        (instructor.full_name, None, True)
    ]

    return render(request, 'course/course_professor.html',
                  {
                      'course': course,
                      'instructor': instructor,
                      'reviews': reviews,
                      'breadcrumbs': breadcrumbs
                  })

from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login
from django.http import JsonResponse
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder

from ..models import School, Department, Course, Semester, Instructor, Review

def browse(request):
    schools = School.objects.all()
    return render(request, 'browse/browse.html', {'schools': schools})

def department(request, dept_id):
    dept = Department.objects.get(pk=dept_id)
    latest_semester = Semester.latest()
    return render(request, 'department/department.html',
        {'department': dept, 'latest_semester': latest_semester})

def course(request, course_id):

    course = Course.objects.get(pk=course_id)
    latest_semester = Semester.latest()
    
    recent_instructor_pks = course.section_set.filter(semester=latest_semester).values_list('instructors', flat=True).distinct()
    recent_instructors = Instructor.objects.filter(pk__in=recent_instructor_pks)

    old_instructor_pks = course.section_set.exclude(semester=latest_semester).exclude(instructors__pk__in=recent_instructor_pks).values_list('instructors', flat=True).distinct()
    old_instructors = Instructor.objects.filter(pk__in=old_instructor_pks)

    return render(request, 'course/course.html',
        {
            'course': course,
            'recent_instructors': recent_instructors,
            'latest_semester': latest_semester,
            'old_instructors': old_instructors
        })

def course_instructor(request, course_id, instructor_id):
    course = Course.objects.get(pk=course_id)
    instructor = Instructor.objects.get(pk=instructor_id)
    reviews = Review.objects.filter(
        instructor=instructor,
        course=course,
    ).exclude(text="").order_by("-created")

    return render(request, 'course/course_professor.html',
        {
            'course': course,
            'instructor': instructor,
            'reviews': reviews,
        })

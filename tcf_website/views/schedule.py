"""View pertaining to schedule creation/viewing."""
import json

from django import forms
# from django.views import generic
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
# from django.contrib.messages.views import SuccessMessageMixin
# from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse
# from django.shortcuts import get_object_or_404, render, redirect
from django.shortcuts import render, redirect
from django.db.models import Prefetch

from .browse import load_secs_helper
from ..models import Schedule, User, Course, Semester, ScheduledCourse, Instructor, Section


class ScheduleForm(forms.ModelForm):
    '''
    Django form for interacting with a schedule
    '''
    user_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Schedule
        fields = [
            'name', 'user_id'
        ]


class SectionForm(forms.ModelForm):
    '''
    Django form for adding a course to a schedule
    '''

    class Meta:
        model = ScheduledCourse
        fields = [
            'schedule', 'section', 'instructor', 'time'
        ]


@login_required
def view_schedules(request):
    '''
    get all schedules, and the related courses, for a given user
    '''

    schedules = Schedule.objects.prefetch_related(
        Prefetch(
            'scheduledcourse_set',
            queryset=ScheduledCourse.objects.select_related('section', 'instructor')
        )
    )
    courses_context = {}

    for s in schedules:
        courses_context[s.id] = s.get_scheduled_courses()

    return render(request, 'schedule/user_schedules.html',
                  {"schedules": schedules, "courses": courses_context})


@login_required
def new_schedule(request):
    '''
    Take the user to the new schedule page
    '''
    if request.method == 'POST':
        # Handle saving the schedule
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            user_id = form.cleaned_data['user_id']  # get the user's primary key
            schedule.user = User.objects.get(id=user_id)
            if user_id == "" or schedule.user is None:
                messages.error(request, "There was an error")
                return render(request, 'schedule/new_schedule.html', {"form": form})
            schedule.save()
            messages.success(request, "Succesfully created schedule!")
            return redirect('schedule')
    else:
        form = ScheduleForm()
    return render(request, 'schedule/new_schedule.html', {"form": form})


@login_required
def modal_load_sections(request):
    '''
    Load the professors and section times for a course when adding to schedule from the modal
    '''
    course_id = request.GET.get('course_id')
    course = Course.objects.get(pk=course_id)
    latest_semester = Semester.latest()

    data = {}
    # section_last_taught = Section.objects\
    #     .filter(course=course_id, instructors=instructor_id)\
    #     .order_by('semester')\
    #     .last()
    instructors = load_secs_helper(
        course, latest_semester).filter(
        semester_last_taught=latest_semester.id)

    for i in instructors:
        temp = {}
        data[i.id] = temp

        # decode the string in section_details and take skip strings without a time or section_id
        encoded_sections = [x for x in i.section_details if x.split(
            ' /% ')[2] != '' and x.split(' /% ')[1] != '']

        temp["sections"] = encoded_sections
        temp["name"] = i.first_name + " " + i.last_name

    return JsonResponse(data)


@login_required
def schedule_add_course(request):
    ''' Add a course to a schedule '''

    if request.method == "POST":
        combined_section_info = json.loads(request.POST['selected_course'])
        form_data = {
            'schedule': request.POST['schedule_id'],
            'instructor': int(combined_section_info['instructor']),
            'section': int(combined_section_info['section']),
            'time': combined_section_info['section_time']
        }
        # make form object with our passed in data
        form = SectionForm(form_data)

        if form.is_valid():
            scheduled_course = form.save(commit=False)
            # extract id's for all related fields
            schedule_id = form.cleaned_data['schedule'].id  # get the schedule's primary key
            instructor_id = form.cleaned_data['instructor'].id  # get the instructor's primary key
            section_id = form.cleaned_data['section'].id  # get the section's primary key
            course_time = form.cleaned_data['section']

            # update the form object with the related objects returned from the database
            # Note: there might be some optimzation where we could do the request in
            # bulk instead of 4 seperate queries
            scheduled_course.schedule = Schedule.objects.get(id=schedule_id)
            scheduled_course.instructor = Instructor.objects.get(id=instructor_id)
            scheduled_course.section = Section.objects.get(id=section_id)
            scheduled_course.time = course_time
            scheduled_course.save()
        else:
            messages.error(request, "Invalid form data")
            return JsonResponse({'status': 'error'}, status=400)

    messages.success(request, "Succesfully added course!")
    return JsonResponse({'status': 'success'})

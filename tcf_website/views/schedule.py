"""View pertaining to schedule creation/viewing."""

import json
import logging

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models import Avg, Case, CharField, Max, Prefetch, Q, Value, When
from django.db.models.functions import Cast, Concat
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from ..models import Course, Instructor, Schedule, ScheduledCourse, Section, Semester

# pylint: disable=line-too-long
# pylint: disable=duplicate-code
# pylint: disable=no-else-return
# pylint: disable=consider-using-generator

logger = logging.getLogger(__name__)


def load_secs_helper(course, latest_semester):
    """Helper function for course_view and for a view in schedule.py"""
    instructors = (
        Instructor.objects.filter(section__course=course, hidden=False)
        .distinct()
        .annotate(
            gpa=Avg(
                "courseinstructorgrade__average",
                filter=Q(courseinstructorgrade__course=course),
            ),
            difficulty=Avg("review__difficulty", filter=Q(review__course=course)),
            rating=(
                Avg("review__instructor_rating", filter=Q(review__course=course))
                + Avg("review__enjoyability", filter=Q(review__course=course))
                + Avg("review__recommendability", filter=Q(review__course=course))
            )
            / 3,
            semester_last_taught=Max(
                "section__semester", filter=Q(section__course=course)
            ),
            # ArrayAgg:
            # https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/aggregates/#arrayagg
            section_times=ArrayAgg(
                Case(
                    When(
                        section__semester=latest_semester,
                        then="section__section_times",
                    ),
                    output_field=CharField(),
                ),
                distinct=True,
            ),
            section_nums=ArrayAgg(
                Case(
                    When(
                        section__semester=latest_semester,
                        then="section__sis_section_number",
                    ),
                    output_field=CharField(),
                ),
                distinct=True,
            ),
            section_details=ArrayAgg(
                # this is to get sections in this format: section.id /%
                # section.section_num /% section.time /% section_type
                Concat(
                    Cast("section__id", CharField()),
                    Value(" /% "),
                    Case(
                        When(
                            section__semester=latest_semester,
                            then=Cast("section__sis_section_number", CharField()),
                        ),
                        default=Value(""),
                        output_field=CharField(),
                    ),
                    Value(" /% "),
                    "section__section_times",
                    Value(" /% "),
                    "section__section_type",
                    Value(" /% "),
                    "section__units",
                    output_field=CharField(),
                ),
                distinct=True,
            ),
        )
    )

    # Note: Refactor pls

    for i in instructors:
        if i.section_times[0] is not None and i.section_nums[0] is not None:
            i.times = {}
            for idx, _ in enumerate(i.section_times):
                if i.section_times[idx] is not None and i.section_nums[idx] is not None:
                    i.times[str(i.section_nums[idx])] = i.section_times[idx][:-1].split(
                        ","
                    )
        if None in i.section_nums:
            i.section_nums.remove(None)

    return instructors


class ScheduleForm(forms.ModelForm):
    """
    Django form for interacting with a schedule
    """

    user_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=15)

    class Meta:
        model = Schedule
        fields = ["name", "user_id"]


class SectionForm(forms.ModelForm):
    """
    Django form for adding a course to a schedule
    """

    class Meta:
        model = ScheduledCourse
        fields = ["schedule", "section", "instructor", "time"]


@login_required
def schedule_data_helper(request):
    """
    This helper method is for getting schedule data for a request.
    """
    schedules = Schedule.objects.filter(user=request.user).prefetch_related(
        Prefetch(
            "scheduledcourse_set",
            queryset=ScheduledCourse.objects.select_related("section", "instructor"),
        )
    )
    courses_context = (
        {}
    )  # contains the joined table for Schedule and ScheduledCourse models
    ratings_context = (
        {}
    )  # contains aggregated ratings for schedules, using the model's method
    difficulty_context = (
        {}
    )  # contains aggregated difficulty of schedules, using the model's method
    credits_context = (
        {}
    )  # contains the total credits of schedules, calculated in this view
    gpa_context = {}  # contains the weighted gpa, calculated in the model function

    # iterate over the schedules for this request in order to set up the context
    # this could also be optimized for the database by combining these queries
    for s in schedules:
        s_data = s.get_schedule()
        courses_context[s.id] = s_data[0]
        credits_context[s.id] = s_data[1]
        ratings_context[s.id] = s_data[2]
        difficulty_context[s.id] = s_data[3]
        gpa_context[s.id] = s_data[4]

    ret = {
        "schedules": schedules,
        "courses": courses_context,
        "ratings": ratings_context,
        "difficulty": difficulty_context,
        "credits": credits_context,
        "schedules_gpa": gpa_context,
    }

    return ret


def view_schedules(request):
    """
    Get all schedules, and the related courses, for a given user.
    """
    schedule_context = schedule_data_helper(request)

    # add an empty schedule form into the context
    # to be used in the create_schedule_modal
    form = ScheduleForm()
    schedule_context["form"] = form

    return render(request, "schedule/user_schedules.html", schedule_context)


def view_select_schedules_modal(request, mode):
    """
    Get all schedules and display in the modal.
    """
    schedule_context = schedule_data_helper(request)

    if mode == "add_course":
        schedule_context["mode"] = mode
    else:
        schedule_context["mode"] = "edit_schedule"
    modal_content = render_to_string(
        "schedule/select_schedule_modal.html", schedule_context, request
    )

    return HttpResponse(modal_content)


@login_required
def new_schedule(request):
    """
    Take the user to the new schedule page.
    """
    if request.method == "POST":
        # Handle saving the schedule
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            if schedule.user is None:
                messages.error(request, "There was an error")
                return render(request, "schedule/user_schedules.html", {"form": form})
            schedule.save()
            messages.success(request, "Successfully created schedule!")
    else:
        # if schedule isn't getting saved, then don't do anything
        # for part two of the this project, load the actual course builder page
        form = ScheduleForm()
    return redirect("schedule")


@login_required
def delete_schedule(request):
    """
    Delete a schedule or multiple schedules.
    """
    # we use POST since forms don't support the DELETE method
    if request.method == "POST":
        # Retrieve IDs from POST data
        schedule_ids = request.POST.getlist("selected_schedules")
        schedule_count = len(schedule_ids)

        # Perform bulk delete
        deleted_count, _ = Schedule.objects.filter(
            id__in=schedule_ids, user=request.user
        ).delete()
        if deleted_count == 0:
            messages.error(request, "No schedules were deleted.")
        else:
            messages.success(
                request,
                f"Successfully deleted {schedule_count} schedules and {deleted_count - schedule_count} courses",
            )
    return redirect("schedule")


@login_required
def duplicate_schedule(request, schedule_id):
    """
    Duplicate a schedule given a schedule id in the request.
    """
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    schedule.pk = None  # reset the key so it will be recreated when it's saved
    old_name = schedule.name
    schedule.name = "Copy of " + old_name
    schedule.save()

    courses = ScheduledCourse.objects.filter(schedule_id=schedule_id)

    for course in courses:
        # loop through all courses and add them to the new schedule
        course.pk = None
        course.schedule = schedule
        course.save()

    messages.success(request, f"Successfully duplicated {old_name}")
    return redirect("schedule")


@login_required
def modal_load_editor(request):
    """
    Load the schedule editor modal with schedule data.
    """
    if request.method != "POST":
        messages.error(request, f"Invalid request method: {request.method}")
        return JsonResponse({"status": "Method Not Allowed"}, status=405)

    body_unicode = request.body.decode("utf-8")
    body = json.loads(body_unicode)
    schedule_id = body.get("schedule_id")

    if not schedule_id:
        messages.error(request, "Schedule ID is missing")
        return JsonResponse({"status": "Bad Request"}, status=400)

    try:
        schedule = Schedule.objects.get(pk=schedule_id)
    except Schedule.DoesNotExist:
        messages.error(request, "Schedule not found")
        return JsonResponse({"status": "Not Found"}, status=404)

    schedule_data = schedule.get_schedule()

    context = {
        "schedule": schedule,
        "schedule_courses": schedule_data[0],
        "schedule_credits": schedule_data[1],
        "schedule_ratings": schedule_data[2],
        "schedule_difficulty": schedule_data[3],
        "schedule_gpa": schedule_data[4],
    }
    return render(request, "schedule/schedule_editor.html", context)


@login_required
def edit_schedule(request):
    """
    Edit a schedule based on a selected schedule, and the changes passed in.
    """
    if request.method != "POST":
        messages.error(request, f"Invalid request method: {request.method}")
        return JsonResponse({"status": "Method Not Allowed"}, status=405)

    schedule = Schedule.objects.get(pk=request.POST["schedule_id"])
    if schedule.name != request.POST["schedule_name"]:
        schedule.name = request.POST["schedule_name"]
        schedule.save()

    deleted_courses = request.POST.getlist("removed_course_ids[]")
    if deleted_courses:
        ScheduledCourse.objects.filter(id__in=deleted_courses).delete()

    messages.success(request, f"Successfully made changes to {schedule.name}")
    return redirect("schedule")


@login_required
def modal_load_sections(request):
    """
    Load the instructors and section times for a course, and the schedule, when adding to schedule from the modal.
    """
    # pylint: disable=too-many-locals
    body_unicode = request.body.decode("utf-8")
    body = json.loads(body_unicode)
    course_id = body["course_id"]
    schedule_id = body["schedule_id"]

    # get the course based off passed in course_id
    course = Course.objects.get(pk=course_id)
    latest_semester = Semester.latest()

    data = {}
    instructors = load_secs_helper(course, latest_semester).filter(
        semester_last_taught=latest_semester.id
    )

    for i in instructors:
        temp = {}
        data[i.id] = temp

        # decode the string in section_details and take skip strings without a time or section_id
        encoded_sections = [
            x.split(" /% ")
            for x in i.section_details
            if x.split(" /% ")[2] != "" and x.split(" /% ")[1] != ""
        ]

        # strip the traling comma
        for section in encoded_sections:
            if section[2].endswith(","):
                section[2] = section[2].rstrip(",")

        temp["sections"] = encoded_sections
        temp["name"] = i.first_name + " " + i.last_name
        temp["rating"] = i.rating
        temp["difficulty"] = i.difficulty
        temp["gpa"] = i.gpa

    schedule = Schedule.objects.get(pk=schedule_id)
    schedule_data = schedule.get_schedule()
    context = {
        "instructors_data": data,
        "schedule": schedule,
        "schedule_courses": schedule_data[0],
        "schedule_credits": schedule_data[1],
        "schedule_ratings": schedule_data[2],
        "schedule_difficulty": schedule_data[3],
        "schedule_gpa": schedule_data[4],
    }
    return render(request, "schedule/schedule_with_sections.html", context)


@login_required
def schedule_add_course(request):
    """Add a course to a schedule, the request should be FormData for the SectionForm class."""

    if request.method == "POST":
        # Parse the JSON-encoded 'selected_course' field
        try:
            selected_course = json.loads(
                request.POST.get("selected_course", "{}")
            )  # Default to empty dict if not found
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )

        form_data = {
            "schedule": request.POST.get("schedule_id"),
            "instructor": int(selected_course.get("instructor")),
            "section": int(selected_course.get("section")),
            "time": selected_course.get("section_time"),
        }

        # make form object with our passed in data
        form = SectionForm(form_data)

        if form.is_valid():
            scheduled_course = form.save(commit=False)
            # extract id's for all related fields
            schedule_id = form.cleaned_data[
                "schedule"
            ].id  # get the schedule's primary key
            instructor_id = form.cleaned_data[
                "instructor"
            ].id  # get the instructor's primary key
            section_id = form.cleaned_data[
                "section"
            ].id  # get the section's primary key
            course_time = form.cleaned_data["time"]

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
            return JsonResponse({"status": "error"}, status=400)

    messages.success(request, "Succesfully added course!")
    return JsonResponse({"status": "success"})

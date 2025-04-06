# pylint disable=bad-continuation
# pylint: disable=too-many-locals

"""Views for Browse, department, and course/course instructor pages."""
import csv
import json
import os
import re
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, CharField, Count, F, Q, Value
from django.db.models.functions import Concat
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..models import (
    Answer,
    Course,
    CourseInstructorGrade,
    Department,
    Instructor,
    Question,
    Review,
    School,
    Section,
    Semester,
)


def browse(request):
    """View for browse page."""
    clas = School.objects.get(name="College of Arts & Sciences")
    seas = School.objects.get(name="School of Engineering & Applied Science")

    excluded_list = [clas.pk, seas.pk]

    # Other schools besides CLAS, SEAS, and Misc.
    other_schools = School.objects.exclude(pk__in=excluded_list).order_by("name")

    return render(
        request,
        "browse/browse.html",
        {
            "CLAS": clas,
            "SEAS": seas,
            "other_schools": other_schools,
        },
    )


def department(request, dept_id: int, course_recency=None):
    """View for department page."""

    # Prefetch related subdepartments and courses to improve performance.
    # department.html loops through related subdepartments and courses.
    # See:
    # https://docs.djangoproject.com/en/3.0/ref/models/querysets/#django.db.models.query.QuerySet.prefetch_related
    dept = Department.objects.prefetch_related("subdepartment_set").get(pk=dept_id)
    # Current semester or last five years
    if not course_recency:
        course_recency = str(Semester.latest())

    # Navigation breadcrimbs
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, None, True),
    ]

    # Setting up sorting and course age variables
    latest_semester = Semester.latest()
    last_five_years = get_object_or_404(Semester, number=latest_semester.number - 50)
    # Fetch season and year (either current semester or 5 years previous)
    season, year = course_recency.upper().split()
    active_semester = Semester.objects.filter(year=year, season=season).first()

    # Fetch sorting variables
    sortby = request.GET.get("sortby", "course_id")
    order = request.GET.get("order", "asc")

    courses = dept.sort_courses(sortby, latest_semester.year - int(year), order)

    return render(
        request,
        "department/department.html",
        {
            "subdepartments": dept.subdepartment_set.all(),
            "dept_id": dept_id,
            "latest_semester": str(latest_semester),
            "breadcrumbs": breadcrumbs,
            "courses": courses,
            "active_course_recency": str(active_semester),
            "sortby": sortby,
            "order": order,
            "last_five_years": str(last_five_years),
        },
    )


def course_view_legacy(request, course_id):
    """Legacy view for course page."""
    course = get_object_or_404(Course, pk=course_id)
    return redirect(
        "course",
        mnemonic=course.subdepartment.mnemonic,
        course_number=course.number,
    )


def course_view(
    request,
    mnemonic: str,
    course_number: int,
    instructor_recency=None,
):
    """A new Course view that allows you to input mnemonic and number instead."""

    if not instructor_recency:
        instructor_recency = str(Semester.latest())

    # Clears previously saved course information
    request.session["course_code"] = None
    request.session["course_title"] = None
    request.session["instructor_fullname"] = None

    # Redirect if the mnemonic is not all uppercase
    if mnemonic != mnemonic.upper():
        return redirect("course", mnemonic=mnemonic.upper(), course_number=course_number)

    course = get_object_or_404(
        Course,
        subdepartment__mnemonic=mnemonic.upper(),
        number=course_number,
    )
    latest_semester = Semester.latest()
    recent = str(latest_semester) == instructor_recency

    # Fetch sorting variables
    sortby = request.GET.get("sortby", "last_taught")
    order = request.GET.get("order", "desc")

    instructors = course.sort_instructors_by_key(latest_semester, recent, order, sortby)

    # Note: Could be simplified further

    for instructor in instructors:
        # Convert to string for templating
        instructor.semester_last_taught = str(
            get_object_or_404(Semester, pk=instructor.semester_last_taught)
        )
        if instructor.section_times[0] and instructor.section_nums[0]:
            instructor.times = {
                num: times[:-1].split(",")
                for num, times in zip(instructor.section_nums, instructor.section_times)
                if num and times
            }

    dept = course.subdepartment.department

    # Navigation breadcrumbs
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, None, True),
    ]

    # Saves information of course to session for recently viewed modal
    request.session["course_code"] = course.code()
    request.session["course_title"] = course.title
    request.session["instructor_fullname"] = None

    return render(
        request,
        "course/course.html",
        {
            "course": course,
            "instructors": instructors,
            "latest_semester": str(latest_semester),
            "breadcrumbs": breadcrumbs,
            "sortby": sortby,
            "order": order,
            "active_instructor_recency": instructor_recency,
        },
    )


def course_instructor(request, course_id, instructor_id, method="Default"):
    """View for course instructor page."""
    section_last_taught = (
        Section.objects.filter(course=course_id, instructors=instructor_id)
        .order_by("semester")
        .last()
    )
    if section_last_taught is None:
        raise Http404
    course = section_last_taught.course
    instructor = section_last_taught.instructors.get(pk=instructor_id)

    # ratings: reviews with and without text; reviews: ratings with text
    reviews = Review.objects.filter(instructor=instructor_id, course=course_id).aggregate(
        num_ratings=Count("id"), num_reviews=Count("id", filter=~Q(text=""))
    )
    num_reviews, num_ratings = reviews["num_reviews"], reviews["num_ratings"]

    dept = course.subdepartment.department

    page_number = request.GET.get("page", 1)
    paginated_reviews = Review.get_paginated_reviews(
        course_id, instructor_id, request.user, page_number, method
    )

    course_url = reverse("course", args=[course.subdepartment.mnemonic, course.number])
    # Navigation breadcrumbs
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, course_url, False),
        (instructor.full_name, None, True),
    ]

    data = Review.objects.filter(course=course_id, instructor=instructor_id).aggregate(
        # rating stats
        average_rating=(Avg("instructor_rating") + Avg("enjoyability") + Avg("recommendability"))
        / 3,
        average_instructor=Avg("instructor_rating"),
        average_fun=Avg("enjoyability"),
        average_recommendability=Avg("recommendability"),
        average_difficulty=Avg("difficulty"),
        # workload stats
        average_hours_per_week=Avg("hours_per_week"),
        average_amount_reading=Avg("amount_reading"),
        average_amount_writing=Avg("amount_writing"),
        average_amount_group=Avg("amount_group"),
        average_amount_homework=Avg("amount_homework"),
    )
    data = {key: safe_round(value) for key, value in data.items()}

    try:
        grades_data = CourseInstructorGrade.objects.get(instructor=instructor, course=course)
    except ObjectDoesNotExist:  # if no data found
        pass
    # NOTE: Don't catch MultipleObjectsReturned because we want to be notified
    else:  # Fill in the data found
        # grades stats
        data["average_gpa"] = round(grades_data.average, 2) if grades_data.average else None
        # pylint: disable=duplicate-code
        fields = [
            "a_plus",
            "a",
            "a_minus",
            "b_plus",
            "b",
            "b_minus",
            "c_plus",
            "c",
            "c_minus",
            "dfw",
            "total_enrolled",
        ]
        for field in fields:
            data[field] = getattr(grades_data, field)

    sections_taught = Section.objects.filter(
        course=course_id,
        instructors__in=Instructor.objects.filter(pk=instructor_id),
        semester=section_last_taught.semester,
    )
    section_info = {
        "year": section_last_taught.semester.year,
        "term": section_last_taught.semester.season.lower().capitalize(),
        "sections": {},
    }
    for section in sections_taught:
        times = []
        for time in section.section_times.split(","):
            if len(time) > 0:
                times.append(time)
        section_info["sections"][section.sis_section_number] = {
            "type": section.section_type,
            "units": section.units,
            "times": times,
        }

    request.session["course_code"] = course.code()
    request.session["course_title"] = course.title
    request.session["instructor_fullname"] = instructor.full_name

    # QA Data
    questions = Question.objects.filter(course=course_id, instructor=instructor_id)
    answers = {}
    for question in questions:
        answers[question.id] = Answer.display_activity(question.id, request.user)
    questions = Question.display_activity(course_id, instructor_id, request.user)

    return render(
        request,
        "course/course_professor.html",
        {
            "course": course,
            "course_id": course_id,
            "instructor": instructor,
            "semester_last_taught": section_last_taught.semester,
            "num_ratings": num_ratings,
            "num_reviews": num_reviews,
            "paginated_reviews": paginated_reviews,
            "breadcrumbs": breadcrumbs,
            "data": json.dumps(data),
            "section_info": section_info,
            "display_times": Semester.latest() == section_last_taught.semester,
            "questions": questions,
            "answers": answers,
            "gpa_history": json.dumps(get_course_term_gpa(course_id, instructor_id)),
            "sort_method": method,
        },
    )


def instructor_view(request, instructor_id):
    """View for instructor page, showing all their courses taught."""
    instructor: Instructor = get_object_or_404(Instructor, pk=instructor_id)

    stats: dict[str, float] = (
        Instructor.objects.filter(pk=instructor_id)
        .prefetch_related("review_set")
        .aggregate(
            avg_gpa=Avg("courseinstructorgrade__average"),
            avg_difficulty=Avg("review__difficulty"),
            avg_rating=(
                Avg("review__instructor_rating")
                + Avg("review__enjoyability")
                + Avg("review__recommendability")
            )
            / 3,
        )
    )

    course_fields: list[str] = [
        "name",
        "id",
        "avg_rating",
        "avg_difficulty",
        "avg_gpa",
        "last_taught",
    ]
    courses: list[dict[str, Any]] = (
        Course.objects.filter(section__instructors=instructor, number__gte=1000)
        .prefetch_related("review_set")
        .annotate(
            subdepartment_name=F("subdepartment__name"),
            name=Concat(
                F("subdepartment__mnemonic"),
                Value(" "),
                F("number"),
                Value(" | "),
                F("title"),
                output_field=CharField(),
            ),
            avg_gpa=Avg(
                "courseinstructorgrade__average",
                filter=Q(courseinstructorgrade__instructor=instructor),
            ),
            avg_difficulty=Avg("review__difficulty", filter=Q(review__instructor=instructor)),
            avg_rating=(
                Avg(
                    "review__instructor_rating",
                    filter=Q(review__instructor=instructor),
                )
                + Avg(
                    "review__enjoyability",
                    filter=Q(review__instructor=instructor),
                )
                + Avg(
                    "review__recommendability",
                    filter=Q(review__instructor=instructor),
                )
            )
            / 3,
            last_taught=Concat(
                F("semester_last_taught__season"),
                Value(" "),
                F("semester_last_taught__year"),
                output_field=CharField(),
            ),
        )
        .values("subdepartment_name", *course_fields)
        .order_by("subdepartment_name", "name")
    )

    grouped_courses: dict[str, list[dict[str, Any]]] = {}
    for course in courses:
        course["avg_rating"] = safe_round(course["avg_rating"])
        course["avg_difficulty"] = safe_round(course["avg_difficulty"])
        course["avg_gpa"] = safe_round(course["avg_gpa"])
        course["last_taught"] = course["last_taught"].title()
        grouped_courses.setdefault(course["subdepartment_name"], []).append(course)

    context: dict[str, Any] = {
        "instructor": instructor,
        **{key: safe_round(value) for key, value in stats.items()},
        "courses": grouped_courses,
    }
    return render(request, "instructor/instructor.html", context)


def safe_round(num):
    """Helper function to reduce syntax repetitions for null checking rounding.

    Returns — if None is passed because that's what appears on the site when there's no data.
    """
    if num is not None:
        return round(num, 2)
    return "\u2014"


# def get_course_term_gpa(course_id, instructor_id):

#     instructor = get_object_or_404(Instructor, instructor_id)
#     course = get_object_or_404(Course, course_id)

#     # course information
#     """
#     title = models.CharField(max_length=255)
#     # Course description. Optional.
#     description = models.TextField(blank=True)
#     # Course disciplines. Optional.
#     disciplines = models.ManyToManyField(Discipline, blank=True)

#     # Course number. Required.
#     number = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99999)])

#     # Subdepartment foreign key. Required.
#     subdepartment = models.ForeignKey(Subdepartment, on_delete=models.CASCADE)
#     # Semester that the course was most recently taught.
#     semester_last_taught = models.ForeignKey(Semester, on_delete=models.CASCADE)
#     # Subdepartment mnemonic and course number. Required.
#     combined_mnemonic_number = models.CharField(max_length=255, blank=True)
#     """

#     # instructor information
#     """
#     # Instructor first_name. Optional.
#     first_name = models.CharField(max_length=255, blank=True)
#     # Instructor last_name. Required.
#     last_name = models.CharField(max_length=255)
#     # Instructor full_name. Auto-populated.
#     full_name = models.CharField(max_length=511, editable=False, blank=True)
#     # Instructor email. Optional.
#     email = models.EmailField(blank=True)
#     # Instructor departments. Optional.
#     departments = models.ManyToManyField(Department)
#     # hidden professor. Required. Default visible.
#     hidden = models.BooleanField(default=False)
#     """

#     csv_folder = "tcf_website/management/commands/grade_data/csv"

#     term_gpa = {}  # maps term (e.g., "2009 Fall") to tuple (weighted_avg, total_enrolled)

#     # Loop over CSV files in the folder
#     for filename in os.listdir(csv_folder):
#         # Consider only CSV files whose filename indicates fall or spring (case-insensitive)
#         if not ("fall" in filename.lower() or "spring" in filename.lower()):
#             continue
#         filepath = os.path.join(csv_folder, filename)
#         with open(filepath, newline="", encoding="utf-8") as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 # Get the term description from the row
#                 term_desc = row.get("Term Desc", "").strip()
#                 # Only process rows for Fall or Spring terms
#                 if not ("fall" in term_desc.lower() or "spring" in term_desc.lower()):
#                     continue

#                 # Check that this row matches the course identifier.
#                 subject = row.get("Subject", "").strip()
#                 catalog_str = re.sub("[^0-9]", "", str(row.get("Catalog Number", "")))
#                 try:
#                     catalog_number = int(catalog_str)
#                 except ValueError:
#                     continue
#                 class_title = row.get("Class Title", "").strip()
#                 if (subject, catalog_number, class_title) != course_id:
#                     continue

#                 # Extract instructor names from "Primary Instructor Name"
#                 primary_instructor = row.get("Primary Instructor Name", "").strip()
#                 try:
#                     last, first_and_middle = primary_instructor.split(",")
#                     first = first_and_middle.split()[0]
#                 except ValueError:
#                     continue
#                 if (first.strip(), last.strip()) != instructor_id:
#                     continue

#                 # At this point the row matches our course and instructor.
#                 # Compute GPA and total enrolled
#                 try:
#                     avg_gpa = float(row["Course GPA"])
#                     total_students = int(row["# of Students"])
#                 except (ValueError, KeyError):
#                     continue

#                 # Update weighted average for this term.
#                 if term_desc in term_gpa:
#                     current_avg, current_total = term_gpa[term_desc]
#                     new_total = current_total + total_students
#                     # Weighted average update:
#                     new_weighted = (
#                         current_avg * current_total + avg_gpa * total_students
#                     ) / new_total
#                     term_gpa[term_desc] = (new_weighted, new_total)
#                 else:
#                     term_gpa[term_desc] = (avg_gpa, total_students)

#     # Convert the stored tuples into a simple dictionary: term -> rounded weighted average GPA.
#     test = {"Fall 2024": 3.389, "Spring 2024": 3.323}

#     transformed = []
#     for term, gpa in test.items():
#         # Assume term format is "Season Year" (e.g. "Fall 2024")
#         parts = term.split()
#         if len(parts) == 2:
#             season, year = parts
#         else:
#             # Fallback if the term is not in expected format
#             season, year = term, ""
#         transformed.append(
#             {
#                 "semester_season": season,
#                 "semester_year": year,
#                 "average_gpa": round(gpa, 2) if gpa is not None else None,
#             }
#         )
#     return transformed


def get_course_term_gpa(course_id, instructor_id):
    # Retrieve the instructor and course objects from the database

    instructor = get_object_or_404(Instructor, pk=instructor_id)
    course = get_object_or_404(Course, pk=course_id)

    csv_folder = "tcf_website/management/commands/grade_data/csv"
    term_gpa = {}

    # Loop over CSV files in the folder
    for filename in os.listdir(csv_folder):
        if not ("fall" in filename.lower() or "spring" in filename.lower()):
            continue
        filepath = os.path.join(csv_folder, filename)
        with open(filepath, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Get the term description from the row
                term_desc = row.get("Term Desc", "").strip()
                # Only process rows for Fall or Spring terms
                if not ("fall" in term_desc.lower() or "spring" in term_desc.lower()):
                    continue

                # Check that this row matches the course identifier.
                subject = row.get("Subject", "").strip()
                catalog_str = re.sub("[^0-9]", "", str(row.get("Catalog Number", "")))
                try:
                    catalog_number = int(catalog_str)
                except ValueError:
                    continue

                combined_mnemonic = f"{subject} {catalog_number}"

                if combined_mnemonic != course.combined_mnemonic_number:
                    continue

                # Extract instructor names from "Primary Instructor Name"
                primary_instructor = row.get("Primary Instructor Name", "").strip()
                try:
                    last, first_and_middle = primary_instructor.split(",")
                    first = first_and_middle.split()[0]
                except ValueError:
                    continue

                full_name = f"{first.strip()} {last.strip()}"

                if full_name != instructor.full_name:
                    continue

                try:
                    gpa_value = float(row.get("Course GPA", 0))
                    enrolled = int(row.get("# of Students", 0))
                except ValueError:
                    continue

                if enrolled <= 0:
                    continue

                # Update term_gpa: accumulate weighted GPA total and total enrollment
                if term_desc not in term_gpa:
                    term_gpa[term_desc] = (0.0, 0)
                weighted_total, total_enrolled = term_gpa[term_desc]
                weighted_total += gpa_value * enrolled
                total_enrolled += enrolled
                term_gpa[term_desc] = (weighted_total, total_enrolled)

    # Compute the final weighted average GPA for each term.
    final_term_gpa = {}
    for term, (weighted_total, total_enrolled) in term_gpa.items():
        if total_enrolled > 0:
            final_term_gpa[term] = weighted_total / total_enrolled

    # Transform the results into the desired output format.
    transformed = []
    for term, gpa in final_term_gpa.items():
        parts = term.split()
        if len(parts) == 2:
            year, season = parts
        else:
            year, season = term, ""
        transformed.append(
            {
                "semester_term": f"{season[0:1]}{year[2:]}",
                "average_gpa": round(gpa, 2) if gpa is not None else None,
            }
        )
    return transformed

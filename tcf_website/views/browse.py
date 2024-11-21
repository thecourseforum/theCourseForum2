# pylint disable=bad-continuation
# pylint: disable=too-many-locals

"""Views for Browse, department, and course/course instructor pages."""
import json
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, CharField, F, Q, Value
from django.db.models.functions import Concat
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..models import Discipline  # Import Discipline model
from ..models import (
    Answer,
    Course,
    CourseInstructorGrade,
    Department,
    Instructor,
    Question,
    Review,
    Section,
    Semester,
    Subdepartment,
)


def browse(request):
    """View for browse page."""

    # Get all semesters from the last 5 years
    latest_semester = Semester.latest()
    recent_semesters = Semester.objects.filter(
        number__gte=latest_semester.number - 50  # 50 = 5 years * 10 semesters
    ).order_by('-number')

    # Get all instructors who have taught in the last 5 years
    recent_instructors = (
        Instructor.objects
        .filter(
            section__semester__number__gte=latest_semester.number - 50,
            hidden=False
        )
        .distinct()
        .order_by('last_name', 'first_name')
    )

    context = {
        'disciplines': Discipline.objects.all().order_by('name'),
        'subdepartments': Subdepartment.objects.all().order_by('mnemonic'),
        'instructors': recent_instructors,
        'semesters': recent_semesters,
        'selected_disciplines': request.GET.getlist('discipline'),
        'selected_subdepartments': request.GET.getlist('subdepartment'),
        'selected_instructors': request.GET.getlist('instructor'),
    }
    return render(request, 'browse/browse.html', context)


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


def course_instructor(request, course_id, instructor_id):
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

    # Find the total number of reviews (with or without text) for the given course
    num_reviews = Review.objects.filter(instructor=instructor_id, course=course_id).count()

    # Filter out reviews with no text and hidden field true.
    reviews = Review.display_reviews(course_id, instructor_id, request.user)
    dept = course.subdepartment.department

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
            "cost": section.cost,
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
            "num_reviews": num_reviews,
            "reviews": reviews,
            "breadcrumbs": breadcrumbs,
            "data": json.dumps(data),
            "section_info": section_info,
            "display_times": Semester.latest() == section_last_taught.semester,
            "questions": questions,
            "answers": answers,
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

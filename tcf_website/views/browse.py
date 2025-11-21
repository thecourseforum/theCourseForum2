# pylint disable=bad-continuation
# pylint: disable=too-many-locals

"""Views for Browse, department, course pages, and course Study Guide."""
import json
from typing import Any

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django import forms
from django.db.models import (
    Avg,
    Count,
    Prefetch,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from storages.backends.s3boto3 import S3Boto3Storage

from ..models import (
    Answer,
    Club,
    ClubCategory,
    Course,
    CourseInstructorGrade,
    Department,
    Instructor,
    Question,
    Review,
    School,
    Section,
    Semester,
    Tag,
    StudyDocument,
)


def browse(request):
    """View for browse page."""
    mode, is_club = parse_mode(request)

    if is_club:
        # Get all club categories
        club_categories = (
            ClubCategory.objects.all()
            .prefetch_related(
                Prefetch(
                    "club_set",
                    queryset=Club.objects.order_by("name"),
                    to_attr="clubs",
                )
            )
            .order_by("name")
        )

        return render(
            request,
            "browse/browse.html",
            {
                "is_club": True,
                "mode": mode,
                "club_categories": club_categories,
            },
        )

    clas = School.objects.get(name="College of Arts & Sciences")
    seas = School.objects.get(name="School of Engineering & Applied Science")

    excluded_list = [clas.pk, seas.pk]

    # Other schools besides CLAS, SEAS, and Misc.
    other_schools = School.objects.exclude(pk__in=excluded_list).order_by("name")

    return render(
        request,
        "browse/browse.html",
        {
            "is_club": False,
            "mode": mode,
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
    page = request.GET.get("page", 1)

    paginated_courses = dept.get_paginated_department_courses(
        sortby, latest_semester.year - int(year), order, page
    )

    return render(
        request,
        "department/department.html",
        {
            # "subdepartments": dept.subdepartment_set.all(),
            "dept_id": dept_id,
            "latest_semester": str(latest_semester),
            "breadcrumbs": breadcrumbs,
            "paginated_courses": paginated_courses,
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


def parse_mode(request):
    """Parse the mode parameter from the request."""
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")


def course_view(
    request,
    mnemonic: str,
    course_number: int,
    instructor_recency=None,
):
    """A new Course view that allows you to input mnemonic and number instead."""

    mode, is_club = parse_mode(request)

    if not instructor_recency:
        instructor_recency = str(Semester.latest())

    # No longer storing in session - client-side storage will handle this
    # (JavaScript now handles this via localStorage)

    if is_club:
        # 'mnemonic' is actually category_slug, 'course_number' is club.id
        club = get_object_or_404(
            Club, id=course_number, category__slug=mnemonic.upper()
        )

        # Pull reviews exactly as you do for courses, but filter on club=club
        page_number = request.GET.get("page", 1)
        paginated_reviews = Review.objects.filter(
            club=club,
            toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
            hidden=False,
        ).exclude(text="")

        if request.user.is_authenticated:
            paginated_reviews = paginated_reviews.annotate(
                sum_votes=Coalesce(Sum("vote__value"), Value(0)),
                user_vote=Coalesce(
                    Sum("vote__value", filter=Q(vote__user=request.user)),
                    Value(0),
                ),
            )

        paginated_reviews = Review.sort(
            paginated_reviews, request.GET.get("method", "")
        )

        paginated_reviews = Review.paginate(paginated_reviews, page_number)

        # Breadcrumbs for club
        breadcrumbs = [
            ("Clubs", reverse("browse") + "?mode=clubs", False),
            (
                club.category.name,
                reverse("club_category", args=[club.category.slug]) + "?mode=clubs",
                False,
            ),
            (club.name, None, True),
        ]

        # Pass club info to template for meta tags
        club_code = f"{club.category.slug} {club.id}"

        return render(
            request,
            "club/club.html",
            {
                "is_club": True,
                "mode": mode,
                "club": club,
                "paginated_reviews": paginated_reviews,
                "sort_method": request.GET.get("method", ""),
                "breadcrumbs": breadcrumbs,
                "course_code": club_code,
                "course_title": club.name,
            },
        )

    # Redirect if the mnemonic is not all uppercase
    if mnemonic != mnemonic.upper():
        return redirect(
            "course", mnemonic=mnemonic.upper(), course_number=course_number
        )

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
    # Remove none values from section_times and section_nums
    # For whatever reason, it is not possible to remove None from .annotate()'s ArrayAgg() function
    for instructor in instructors:
        if hasattr(instructor, "section_times") and instructor.section_times:
            instructor.section_times = [
                s for s in instructor.section_times if s is not None
            ]

        if hasattr(instructor, "section_nums") and instructor.section_nums:
            instructor.section_nums = [
                s for s in instructor.section_nums if s is not None
            ]

    # Note: Could be simplified further

    for instructor in instructors:
        # Convert to string for templating
        instructor.semester_last_taught = str(
            get_object_or_404(Semester, pk=instructor.semester_last_taught)
        )
        if instructor.section_times and instructor.section_nums:
            if instructor.section_times[0] and instructor.section_nums[0]:
                instructor.times = {
                    num: times[:-1].split(",")
                    for num, times in zip(
                        instructor.section_nums, instructor.section_times
                    )
                    if num and times
                }

    dept = course.subdepartment.department

    # Navigation breadcrumbs
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, None, True),
    ]

    # Pass course info to template for meta tags
    # (JavaScript will retrieve these from meta tags)

    return render(
        request,
        "course/course.html",
        {
            "is_club": False,
            "mode": mode,
            "course": course,
            "instructors": instructors,
            "latest_semester": str(latest_semester),
            "breadcrumbs": breadcrumbs,
            "sortby": sortby,
            "order": order,
            "active_instructor_recency": instructor_recency,
            "course_code": course.code(),
            "course_title": course.title,
        },
    )


class StudyDocumentForm(forms.ModelForm):
    """Simple model form for uploading course study documents.

    Includes a free-form comma-separated tags field that we will parse and
    map to Tag objects.
    """

    # Dynamic multi-select of Tag objects, populated by the view
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control",
            "id": "id_tags",
            "size": "8",
        }),
        label="Tags",
        help_text="Select one or more tags",
    )

    class Meta:
        model = StudyDocument
        fields = ["title", "description", "file", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Document title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Brief description (optional)"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }

    def __init__(self, *args, **kwargs):
        tag_queryset = kwargs.pop("tag_queryset", None)
        super().__init__(*args, **kwargs)
        if tag_queryset is not None:
            self.fields["tags"].queryset = tag_queryset.order_by("name")
        # Dev-only storage toggle (local vs S3)
        from django.conf import settings as dj_settings
        environment = getattr(dj_settings, "ENVIRONMENT", "development")
        if environment != "production":
            self.fields["storage_target"] = forms.ChoiceField(
                choices=[("local", "Store locally"), ("s3", "Send to S3")],
                required=False,
                initial="local",
                label="Storage",
                widget=forms.RadioSelect,
            )

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f is None:
            return f
        max_mb = 25
        if f.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(f"File too large. Max {max_mb}MB.")
        # Basic content-type allowlist
        allowed = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        }
        content_type = getattr(f, "content_type", None)
        if content_type and content_type not in allowed:
            raise forms.ValidationError("Unsupported file type.")
        return f


def study_guide(request, mnemonic: str, course_number: int):
    """Study guide page for a course.

    Displays a per-course hub for study documents and uploads.
    Refactored to show listing and tag filters. Uploads moved to dedicated page.
    """

    # Redirect if mnemonic is not uppercase for consistency
    if mnemonic != mnemonic.upper():
        return redirect("study_guide", mnemonic=mnemonic.upper(), course_number=course_number)

    course = get_object_or_404(
        Course,
        subdepartment__mnemonic=mnemonic.upper(),
        number=course_number,
    )

    dept = course.subdepartment.department
    # Build breadcrumbs mirroring course page, with Study Guide as final crumb
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, reverse("course", args=[course.subdepartment.mnemonic, course.number]), False),
        ("Study Guide", None, True),
    ]

    # Handle filtering by tag
    tag_query = request.GET.get("tag", "").strip().lower()
    documents = StudyDocument.objects.filter(course=course).order_by("-created_at")
    active_tag = None
    if tag_query:
        active_tag = Tag.objects.filter(name=tag_query).first()
        if active_tag:
            documents = documents.filter(tags=active_tag)
        else:
            documents = documents.none()

    # No uploads handled here; dedicated upload page handles POST/GET

    return render(
        request,
        "course/study_guide.html",
        {
            "course": course,
            "breadcrumbs": breadcrumbs,
            # Meta values used by recently_viewed client script
            "course_code": course.code(),
            "course_title": course.title,
            "documents": documents,
            "active_tag": active_tag.name if active_tag else "",
            # Upload moved to separate page
        },
    )


def study_guide_upload(request, mnemonic: str, course_number: int):
    """Upload page for course study documents."""

    # Redirect if mnemonic is not uppercase for consistency
    if mnemonic != mnemonic.upper():
        return redirect("study_guide_upload", mnemonic=mnemonic.upper(), course_number=course_number)

    course = get_object_or_404(
        Course,
        subdepartment__mnemonic=mnemonic.upper(),
        number=course_number,
    )

    dept = course.subdepartment.department
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, reverse("course", args=[course.subdepartment.mnemonic, course.number]), False),
        ("Upload Document", None, True),
    ]

    upload_error = None

    # Build available tags: defaults + instructor names
    default_tags = ["notes", "homework", "exam"]
    latest_semester = Semester.latest()
    instructor_names = (
        Instructor.objects.filter(section__course=course, section__semester=latest_semester)
        .distinct()
        .values_list("full_name", flat=True)
    )
    candidate_names = default_tags + [n.lower() for n in instructor_names]
    # Ensure Tag objects exist for each candidate
    for name in candidate_names:
        if name:
            Tag.objects.get_or_create(name=name.strip().lower())
    tag_qs = Tag.objects.filter(name__in=[n.strip().lower() for n in candidate_names])
    if request.method == "POST":
        form = StudyDocumentForm(request.POST, request.FILES, tag_queryset=tag_qs)
        if form.is_valid():
            doc: StudyDocument = form.save(commit=False)
            doc.course = course
            if request.user.is_authenticated:
                doc.uploader = request.user
            f = doc.file
            try:
                doc.mime_type = getattr(f, "content_type", "")
                doc.size = getattr(f, "size", 0) or 0
            except Exception:  # pylint: disable=broad-except
                doc.size = 0
            # Decide storage target (dev only toggle)
            environment = getattr(settings, "ENVIRONMENT", "development")
            selected_storage = form.cleaned_data.get("storage_target", "local")
            saved_ok = False
            if environment != "production" and selected_storage == "s3":
                # Ensure S3 is configured
                required_keys = [
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "AWS_STORAGE_BUCKET_NAME",
                ]
                if not all(getattr(settings, k, None) for k in required_keys):
                    upload_error = "S3 is not configured in development. Please set AWS_* env vars."
                else:
                    file_field = StudyDocument._meta.get_field("file")
                    original_storage = file_field.storage
                    try:
                        file_field.storage = S3Boto3Storage()
                        doc.save()
                        saved_ok = True
                    finally:
                        file_field.storage = original_storage
            else:
                doc.save()
                saved_ok = True

            if saved_ok:
                # Assign selected tags
                selected_tags = form.cleaned_data.get("tags")
                if selected_tags is not None:
                    doc.tags.set(selected_tags)

                return redirect("study_guide", mnemonic=course.subdepartment.mnemonic, course_number=course.number)
            # else: fall through and re-render with error
        else:
            upload_error = "There was a problem with your upload. Please check the file and fields."
    else:
        form = StudyDocumentForm(tag_queryset=tag_qs)

    return render(
        request,
        "course/study_guide_upload.html",
        {
            "course": course,
            "breadcrumbs": breadcrumbs,
            "course_code": course.code(),
            "course_title": course.title,
            "form": form,
            "upload_error": upload_error,
            "is_dev": getattr(settings, "ENVIRONMENT", "development") != "production",
        },
    )


def course_instructor(request, course_id, instructor_id, method="Default"):
    """View for course instructor page."""
    section_last_taught = (
        Section.objects.filter(course=course_id, instructors=instructor_id)
        .order_by("-semester__number")
        .first()
    )
    if section_last_taught is None:
        raise Http404
    course = section_last_taught.course
    instructor = section_last_taught.instructors.get(pk=instructor_id)

    # ratings: reviews with and without text; reviews: ratings with text
    reviews = Review.objects.filter(
        instructor=instructor_id,
        course=course_id,
        toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
    ).aggregate(num_ratings=Count("id"), num_reviews=Count("id", filter=~Q(text="")))
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
        average_rating=(
            Avg("instructor_rating") + Avg("enjoyability") + Avg("recommendability")
        )
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
        grades_data = CourseInstructorGrade.objects.get(
            instructor=instructor, course=course
        )
    except ObjectDoesNotExist:  # if no data found
        pass
    # NOTE: Don't catch MultipleObjectsReturned because we want to be notified
    else:  # Fill in the data found
        # grades stats
        data["average_gpa"] = (
            round(grades_data.average, 2) if grades_data.average else None
        )
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

    # No longer storing in session
    # Course and instructor info is passed to template context for meta tags
    # Sections will be fetched via API when dropdown is expanded

    # QA Data
    questions = Question.objects.filter(course=course_id, instructor=instructor_id)
    answers = {}
    for question in questions:
        answers[question.id] = Answer.display_activity(question.id, request.user)
    questions = Question.display_activity(course_id, instructor_id, request.user)

    latest_semester = Semester.latest()
    is_current_semester = section_last_taught.semester.number == latest_semester.number

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
            "display_times": latest_semester == section_last_taught.semester,
            "is_current_semester": is_current_semester,
            "questions": questions,
            "answers": answers,
            "sort_method": method,
            "sem_code": section_last_taught.semester.number,
            "latest_semester_id": latest_semester.id,
            "course_code": course.code(),
            "course_title": course.title,
            "instructor_fullname": instructor.full_name,
        },
    )


def instructor_view(request, instructor_id):
    """View for instructor page, showing all their courses taught."""
    instructor: Instructor = get_object_or_404(Instructor, pk=instructor_id)

    stats: dict[str, float] = Instructor.objects.filter(pk=instructor.pk).aggregate(
        avg_gpa=Avg("courseinstructorgrade__average"),
        avg_difficulty=Avg("review__difficulty"),
        avg_rating=(
            Avg("review__instructor_rating")
            + Avg("review__enjoyability")
            + Avg("review__recommendability")
        )
        / 3,
    )

    courses = list(instructor.get_course_summaries())
    is_teaching_current_semester = any(course.get("is_current") for course in courses)

    # Build a mapping from semester number to (season, year) in one query
    semester_numbers = {
        num for num in (c.get("latest_semester_number") for c in courses) if num
    }
    semester_info = {
        s["number"]: (s["season"], s["year"])
        for s in Semester.objects.filter(number__in=semester_numbers).values(
            "number", "season", "year"
        )
    }

    grouped_courses: dict[str, list[dict[str, Any]]] = {}
    for course in courses:
        course["avg_rating"] = safe_round(course["avg_rating"])
        course["avg_difficulty"] = safe_round(course["avg_difficulty"])
        course["avg_gpa"] = safe_round(course["avg_gpa"])
        sem_num = course.pop("latest_semester_number", None)
        if sem_num and sem_num in semester_info:
            season, year = semester_info[sem_num]
            course["last_taught"] = f"{season} {year}".title()
        else:
            course["last_taught"] = "—"

        grouped_courses.setdefault(course["subdepartment_name"], []).append(course)

    context: dict[str, Any] = {
        "instructor": instructor,
        **{key: safe_round(value) for key, value in stats.items()},
        "courses": grouped_courses,
        "is_teaching_current_semester": is_teaching_current_semester,
    }
    return render(request, "instructor/instructor.html", context)


def safe_round(num):
    """Helper function to reduce syntax repetitions for null checking rounding.

    Returns — if None is passed because that's what appears on the site when there's no data.
    """
    if num is not None:
        return round(num, 2)
    return "\u2014"


def club_category(request, category_slug: str):
    """View for club category page."""
    mode = parse_mode(request)[0]  # Only use the mode, ignoring is_club

    # Get the category by slug
    category = get_object_or_404(ClubCategory, slug=category_slug.upper())

    # Get clubs in this category
    clubs = Club.objects.filter(category=category).order_by("name")

    # Pagination
    page_number = request.GET.get("page", 1)
    paginator = Paginator(clubs, 10)  # 10 clubs per page
    try:
        paginated_clubs = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_clubs = paginator.page(1)
    except EmptyPage:
        paginated_clubs = paginator.page(paginator.num_pages)

    # Navigation breadcrumbs
    breadcrumbs = [
        ("Clubs", reverse("browse") + "?mode=clubs", False),
        (category.name, None, True),
    ]

    return render(
        request,
        "club/category.html",
        {
            "is_club": True,
            "mode": mode,
            "category": category,
            "paginated_clubs": paginated_clubs,
            "breadcrumbs": breadcrumbs,
        },
    )

"""View pertaining to review creation/viewing."""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST

from ..models import Review, Club, Course, Instructor, Section, Semester
from ..utils import (
    parse_mode,
    recent_semesters,
    safe_next_url,
    semesters_for_course,
    with_mode,
)

# pylint: disable=fixme,unused-argument


class ReviewForm(forms.ModelForm):
    """Form for review creation in the backend, not for rendering HTML."""

    class Meta:
        model = Review
        fields = [
            "text",
            "course",
            "club",
            "instructor",
            "semester",
            "instructor_rating",
            "difficulty",
            "recommendability",
            "enjoyability",
            "amount_reading",
            "amount_writing",
            "amount_group",
            "amount_homework",
        ]

    def clean(self):
        """Validate that either club or (course and instructor) are provided."""
        cleaned_data = super().clean()
        club = cleaned_data.get("club")
        course = cleaned_data.get("course")
        instructor = cleaned_data.get("instructor")
        semester = cleaned_data.get("semester")

        # If it's a club review, course and instructor are not required
        if club:
            return cleaned_data

        # If it's a course review, both course and instructor are required
        if not course:
            raise ValidationError("Course is required for course reviews")
        if not instructor:
            raise ValidationError("Instructor is required for course reviews")
        if not semester:
            raise ValidationError("Semester is required for course reviews")

        if not Section.objects.filter(
            course=course, semester=semester, instructors=instructor
        ).exists():
            raise ValidationError(
                "Selected instructor did not teach this course in the chosen semester."
            )

        return cleaned_data

    def save(self, commit=True):
        """Compute `hours_per_week` before actually saving"""
        instance = super().save(commit=False)
        instance.hours_per_week = (
            instance.amount_reading
            + instance.amount_writing
            + instance.amount_group
            + instance.amount_homework
        )
        if commit:
            instance.save()
        return instance


def _review_preflight_wants_json(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _review_preflight_invalid_form_response(request, form: ReviewForm):
    if _review_preflight_wants_json(request):
        return JsonResponse(
            {
                "ok": False,
                "error": "Invalid review data.",
                "errors": form.errors.get_json_data(),
            },
            status=400,
        )
    return redirect("new_review")


def _vote_response_payload(review: Review, user) -> dict[str, int]:
    """Return vote state payload for frontend updates."""
    agg = review.vote_set.aggregate(
        sum_votes=Coalesce(Sum("value"), 0),
        user_vote=Coalesce(Sum("value", filter=Q(user=user)), 0),
    )
    return {"ok": True, "sum_votes": agg["sum_votes"], "user_vote": agg["user_vote"]}


@login_required
@require_POST
def upvote(request, review_id):
    """Upvote a view."""
    review = get_object_or_404(Review, pk=review_id)
    review.upvote(request.user)
    return JsonResponse(_vote_response_payload(review, request.user))


@login_required
@require_POST
def downvote(request, review_id):
    """Downvote a view."""
    review = get_object_or_404(Review, pk=review_id)
    review.downvote(request.user)
    return JsonResponse(_vote_response_payload(review, request.user))


@login_required
@require_POST
def vote_review(request, review_id):
    """Vote on a review using a single endpoint."""
    review = get_object_or_404(Review, pk=review_id)
    action = request.POST.get("action")

    if action == "up":
        review.upvote(request.user)
    elif action == "down":
        review.downvote(request.user)
    else:
        return JsonResponse({"ok": False, "error": "Invalid action"}, status=400)

    return JsonResponse(_vote_response_payload(review, request.user))


@login_required()
def check_duplicate(request):
    """Check for duplicate reviews when a user submits a review."""

    form = ReviewForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)

        if instance.club:
            # Check if user has reviewed given club before
            reviews_on_same_club = request.user.review_set.filter(club=instance.club)
            # Review already exists so it's a duplicate; inform user
            if reviews_on_same_club.exists():
                return JsonResponse({"duplicate": True})
            return JsonResponse({"duplicate": False})

        # First check if user has reviewed given course during same
        # semester before
        reviews_on_same_class = request.user.review_set.filter(
            course=instance.course, semester=instance.semester
        )

        # Review already exists so it's a duplicate; inform user
        if reviews_on_same_class.exists():
            response = {"duplicate": True}
            return JsonResponse(response)

        # Then check if user has reviewed given course with same
        # instructor before
        reviews_on_same_class = request.user.review_set.filter(
            course=instance.course, instructor=instance.instructor
        )
        # Review already exists so it's a duplicate; inform user
        if reviews_on_same_class.exists():
            response = {"duplicate": True}
            return JsonResponse(response)

        # User has not reviewed course/club before; proceed with standard form submission
        response = {"duplicate": False}
        return JsonResponse(response)
    return _review_preflight_invalid_form_response(request, form)


@login_required()
def check_zero_hours_per_week(request):
    """Check that user hasn't submitted 0 *total* hours/week
    for a given course/review.
    Used for an Ajax request in new_review.html"""

    form = ReviewForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)

        # Review has 0 total hours/week
        # Send user a warning message that they have entered 0 hours
        if instance.hours_per_week == 0:
            response = {"zero": True}
            return JsonResponse(response)

        # Otherwise, proceed with normal form submission
        response = {"zero": False}
        return JsonResponse(response)
    return _review_preflight_invalid_form_response(request, form)


def _recent_semester_id_set() -> set[int]:
    return set(recent_semesters().values_list("pk", flat=True))


def _club_semester_choices_payload():
    """JSON-serializable term rows for club-mode review (inline club pick)."""
    return [{"id": s.id, "label": str(s)} for s in recent_semesters()]


def instructors_for_course_semester(course_id: int, semester_id: int):
    """Instructors with a section for this course in this semester."""
    return (
        Instructor.objects.filter(
            section__course_id=course_id,
            section__semester_id=semester_id,
            hidden=False,
        )
        .distinct()
        .order_by("last_name", "first_name")
    )


@login_required
def review_semester_options(request):
    """Return terms (recent catalog window) in which a course has at least one section."""
    try:
        course_id = int(request.GET["course"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "course required"}, status=400)

    course = get_object_or_404(Course, id=course_id)
    rows = [{"id": s.id, "label": str(s)} for s in semesters_for_course(course)]
    return JsonResponse({"semesters": rows})


@login_required
def review_instructor_options(request):
    """Return instructors teaching a course in a semester (for review cascade XHR)."""
    try:
        course_id = int(request.GET["course"])
        semester_id = int(request.GET["semester"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "course and semester required"}, status=400)

    if semester_id not in _recent_semester_id_set():
        return JsonResponse({"error": "invalid semester"}, status=400)

    get_object_or_404(Course, id=course_id)

    rows = [
        {"id": i.id, "last_name": i.last_name, "first_name": i.first_name}
        for i in instructors_for_course_semester(course_id, semester_id)
    ]
    return JsonResponse({"instructors": rows})


# Note: Class-based views can't use the @login_required decorator


class DeleteReview(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Review deletion view."""

    model = Review
    success_url = reverse_lazy("reviews")

    def get_success_url(self):
        """Use caller-provided next URL when safe, otherwise default."""
        return safe_next_url(self.request, str(self.success_url))

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate review belonging to user."""
        obj = super().get_object()
        # For security: Make sure target review belongs to the current user
        if obj.user != self.request.user:
            raise PermissionDenied("You are not allowed to delete this review!")
        return obj

    def get_success_message(self, cleaned_data) -> str:
        """Overrides SuccessMessageMixin's get_success_message method."""
        # Check if it's a club review
        if self.object.club:
            return f"Successfully deleted your review for {self.object.club}!"
        return f"Successfully deleted your review for {self.object.course}!"


@login_required
def new_review(request):
    """Review creation view with context-required logic."""
    mode, is_club = parse_mode(request)

    # Handle POST (form submission)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.hours_per_week = (
                instance.amount_reading
                + instance.amount_writing
                + instance.amount_group
                + instance.amount_homework
            )
            instance.save()

            # Success message
            if instance.club:
                messages.success(request, f"Successfully reviewed {instance.club}!")
            else:
                messages.success(request, f"Successfully reviewed {instance.course}!")

            # Redirect to the new relevant page
            if instance.club:
                club_url = reverse(
                    "club",
                    kwargs={
                        "category_slug": instance.club.category.slug,
                        "club_id": instance.club.id,
                    },
                )
                return redirect(with_mode(club_url, "clubs"))
            return redirect(
                "course",
                mnemonic=instance.course.subdepartment.mnemonic,
                course_number=instance.course.number,
            )

        # Form invalid - re-render with errors
        return _render_review_form_with_errors(request, form, is_club, mode)

    # Handle GET
    if is_club:
        return _handle_club_review_get(request, mode)
    return _handle_course_review_get(request, mode)


def _handle_course_review_get(request, mode):
    """Handle GET for course reviews."""
    course_id = request.GET.get("course")
    instructor_id = request.GET.get("instructor")

    if not course_id:
        return render(
            request,
            "site/pages/review.html",
            {
                "is_club": False,
                "mode": mode,
                "course": None,
                "club": None,
                "instructor": None,
                "instructors": [],
                "semesters": recent_semesters(),
                "review_main_unlocked": False,
            },
        )

    course = get_object_or_404(
        Course.objects.select_related("subdepartment"), id=course_id
    )
    semesters = semesters_for_course(course)
    prefill_instructor = None
    prefill_semester = None
    instructors_list = []
    if instructor_id:
        prefill_instructor = get_object_or_404(Instructor, id=instructor_id)
        prefill_semester = semesters.filter(
            section__instructors=prefill_instructor
        ).first()
        if prefill_semester:
            instructors_list = list(
                instructors_for_course_semester(course.id, prefill_semester.id)
            )

    return render(
        request,
        "site/pages/review.html",
        {
            "is_club": False,
            "mode": mode,
            "course": course,
            "club": None,
            "instructor": None,
            "prefill_instructor": prefill_instructor,
            "prefill_semester": prefill_semester,
            "instructors": instructors_list,
            "semesters": semesters,
            "review_main_unlocked": False,
        },
    )


def _handle_club_review_get(request, mode):
    """Handle GET for club reviews."""
    club_id = request.GET.get("club")
    semesters = recent_semesters()

    if not club_id:
        return render(
            request,
            "site/pages/review.html",
            {
                "is_club": True,
                "mode": mode,
                "club": None,
                "course": None,
                "semesters": semesters,
                "club_semester_choices": _club_semester_choices_payload(),
                "review_main_unlocked": False,
            },
        )

    club = get_object_or_404(Club.objects.select_related("category"), id=club_id)

    return render(
        request,
        "site/pages/review.html",
        {
            "is_club": True,
            "mode": mode,
            "club": club,
            "course": None,
            "semesters": semesters,
            "club_semester_choices": _club_semester_choices_payload(),
            "review_main_unlocked": True,
        },
    )


def _render_review_form_with_errors(request, form, is_club, mode):
    """Re-render the form with validation errors."""
    context: dict = {"form": form, "is_club": is_club, "mode": mode}
    base_semesters = recent_semesters()

    if is_club:
        club = form.cleaned_data.get("club")
        if not club:
            raw = form.data.get("club")
            club = (
                Club.objects.filter(pk=raw).select_related("category").first()
                if raw
                else None
            )
        context["club"] = club
        context["course"] = None
        context["instructor"] = None
        context["semesters"] = base_semesters
        context["instructors"] = []
        context["club_semester_choices"] = _club_semester_choices_payload()
        context["review_main_unlocked"] = bool(form.errors) or bool(
            form.data.get("club") and form.data.get("semester")
        )
        return render(request, "site/pages/review.html", context)

    course = form.cleaned_data.get("course")
    if not course:
        raw = form.data.get("course")
        course = (
            Course.objects.filter(pk=raw).select_related("subdepartment").first()
            if raw
            else None
        )

    if not course:
        context["course"] = None
        context["club"] = None
        context["instructor"] = None
        context["semesters"] = base_semesters
        context["instructors"] = []
        context["review_main_unlocked"] = bool(form.errors)
        return render(request, "site/pages/review.html", context)

    context["course"] = course
    context["club"] = None
    instructor = form.cleaned_data.get("instructor")
    if not instructor:
        iid = form.data.get("instructor")
        instructor = Instructor.objects.filter(pk=iid).first() if iid else None
    context["instructor"] = instructor

    context["semesters"] = semesters_for_course(course)

    semester = form.cleaned_data.get("semester")
    if not semester:
        sid = form.data.get("semester")
        semester = Semester.objects.filter(pk=sid).first() if sid else None
    if semester:
        context["instructors"] = list(
            instructors_for_course_semester(course.id, semester.id)
        )
    else:
        context["instructors"] = []

    context["review_main_unlocked"] = bool(form.errors) or bool(
        form.data.get("course")
        and form.data.get("semester")
        and form.data.get("instructor")
    )

    return render(request, "site/pages/review.html", context)

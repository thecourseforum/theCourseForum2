"""View pertaining to review creation/viewing."""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import generic

from ..models import Review, Club, Course, Instructor, Semester

# pylint: disable=fixme,unused-argument


def parse_mode(request):
    """Parse the mode parameter from the request."""
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")


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

        # If it's a club review, course and instructor are not required
        if club:
            return cleaned_data

        # If it's a course review, both course and instructor are required
        if not course:
            raise ValidationError("Course is required for course reviews")
        if not instructor:
            raise ValidationError("Instructor is required for course reviews")

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


@login_required
def upvote(request, review_id):
    """Upvote a view."""
    if request.method == "POST":
        review = Review.objects.get(pk=review_id)
        review.upvote(request.user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})


@login_required
def downvote(request, review_id):
    """Downvote a view."""
    if request.method == "POST":
        review = Review.objects.get(pk=review_id)
        review.downvote(request.user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})


@login_required
def new_review(request):
    """Review creation view with context-required logic.

    Routes:
    - /reviews/new/?course=X&instructor=Y → Full form, server-rendered
    - /reviews/new/?club=Z → Full club review form
    - /reviews/new/
    """
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

            return redirect("reviews")

        # Form invalid - re-render with errors
        # Need to re-fetch context for the template
        return _render_review_form_with_errors(request, form, is_club, mode)

    # Handle GET - require context or redirect to search
    if is_club:
        return _handle_club_review_get(request, mode)
    return _handle_course_review_get(request, mode)


def _handle_course_review_get(request, mode):
    """Handle GET for course reviews - require course context."""
    course_id = request.GET.get("course")
    instructor_id = request.GET.get("instructor")

    # No context - need course ID, redirect to home
    if not course_id:
        messages.info(request, "Please select a course to review from a course page.")
        return redirect("/browse?mode=courses")

    course = get_object_or_404(Course, id=course_id)
    latest = Semester.latest()

    if instructor_id:
        # Full context: course + instructor
        instructor = get_object_or_404(Instructor, id=instructor_id)
        instructors = None
        # Semesters when this instructor taught this course (last 5 years)
        semesters = (
            Semester.objects.filter(
                section__course=course,
                section__instructors=instructor,
                year__gte=latest.year - 5,
            )
            .distinct()
            .order_by("-number")
        )
    else:
        # Partial context: only course - let user pick instructor
        instructor = None
        instructors = (
            Instructor.objects.filter(
                section__course=course,
                section__semester__year__gte=latest.year - 5,
                hidden=False,
            )
            .distinct()
            .order_by("last_name")[:50]
        )
        # All recent semesters for this course
        semesters = (
            Semester.objects.filter(section__course=course, year__gte=latest.year - 5)
            .distinct()
            .order_by("-number")
        )

    return render(
        request,
        "reviews/new_review.html",
        {
            "is_club": False,
            "mode": mode,
            "course": course,
            "instructor": instructor,
            "instructors": instructors,
            "semesters": semesters,
        },
    )


def _handle_club_review_get(request, mode):
    """Handle GET for club reviews - require club context."""
    club_id = request.GET.get("club")

    # No context - need club ID, redirect to home
    if not club_id:
        messages.info(request, "Please select a club to review.")
        return redirect("/browse?mode=clubs")

    club = get_object_or_404(Club, id=club_id)
    latest = Semester.latest()

    # Recent semesters for the dropdown
    semesters = Semester.objects.filter(year__gte=latest.year - 5).order_by("-number")[
        :10
    ]

    return render(
        request,
        "reviews/new_review.html",
        {
            "is_club": True,
            "mode": mode,
            "club": club,
            "semesters": semesters,
        },
    )


def _render_review_form_with_errors(request, form, is_club, mode):
    """Re-render the form with validation errors, fetching context from POST data."""
    context = {"form": form, "is_club": is_club, "mode": mode}

    if is_club and form.cleaned_data.get("club"):
        context["club"] = form.cleaned_data["club"]
    elif form.cleaned_data.get("course"):
        context["course"] = form.cleaned_data["course"]
        context["instructor"] = form.cleaned_data.get("instructor")

    # Fetch semesters for re-render
    latest = Semester.latest()
    context["semesters"] = Semester.objects.filter(year__gte=latest.year - 5).order_by(
        "-number"
    )[:10]

    return render(request, "reviews/new_review.html", context)


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
    return redirect("new_review")


@login_required()
def check_zero_hours_per_week(request):
    """Check that user hasn't submitted 0 *total* hours/week
    for a given course/review.
    Used for an Ajax request in new_review.html"""

    form = ReviewForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)

        hours_per_week = (
            instance.amount_reading
            + instance.amount_writing
            + instance.amount_group
            + instance.amount_homework
        )

        # Review has 0 total hours/week
        # Send user a warning message that they have entered 0 hours
        if hours_per_week == 0:
            response = {"zero": True}
            return JsonResponse(response)

        # Otherwise, proceed with normal form submission
        response = {"zero": False}
        return JsonResponse(response)
    return redirect("new_review")


# Note: Class-based views can't use the @login_required decorator


class DeleteReview(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Review deletion view."""

    model = Review
    success_url = reverse_lazy("reviews")

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

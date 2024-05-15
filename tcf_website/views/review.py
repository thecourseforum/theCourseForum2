"""View pertaining to review creation/viewing."""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (  # For class-based views
    LoginRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import generic

from ..models import Review

# pylint: disable=fixme,unused-argument
# Disable pylint errors on TODO messages, such as below

# TODO: use a proper django form, make it more robust.
# (i.e. better Course/Instructor/Semester search).


class ReviewForm(forms.ModelForm):
    """Form for review creation in the backend, not for rendering HTML."""

    class Meta:
        model = Review
        fields = [
            "text",
            "course",
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
    """Review creation view."""

    # Collect form data into Review model instance.
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

            messages.success(
                request, f"Successfully reviewed {instance.course}!"
            )
            return redirect("reviews")
        return render(request, "reviews/new_review.html", {"form": form})
    return render(request, "reviews/new_review.html")


@login_required()
def check_duplicate(request):
    """Check for duplicate reviews when a user submits a review
    based on if it's the same course with the same instructor/semester.
    Used for an Ajax request in new_review.html"""

    form = ReviewForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)

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

        # User has not reviewed course during same semester OR with same instructor before;
        # proceed with standard form submission
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
        # get the course this review is about
        course = self.object.course

        # return success message
        return f"Successfully deleted your review for {str(course)}!"


@login_required
def edit_review(request, review_id):
    """Review modification view."""
    review = get_object_or_404(Review, pk=review_id)
    if review.user != request.user:
        raise PermissionDenied("You are not allowed to edit this review!")

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Successfully updated your review for {form.instance.course}!",
            )
            return redirect("reviews")
        messages.error(request, form.errors)
        return render(request, "reviews/edit_review.html", {"form": form})
    form = ReviewForm(instance=review)
    return render(request, "reviews/edit_review.html", {"form": form})

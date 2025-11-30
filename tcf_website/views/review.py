"""View pertaining to review creation/viewing."""

from django.db import IntegrityError
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

from ..models import Review, Reply, ClubCategory, Club

# pylint: disable=fixme,unused-argument
# Disable pylint errors on TODO messages, such as below

# TODO: use a proper django form, make it more robust.
# (i.e. better Course/Instructor/Semester search).


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
    """Review creation view."""
    mode, is_club = parse_mode(request)

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

            # Determine redirect URL with appropriate mode
            redirect_url = "reviews"

            # Check if this is a club review by directly checking if club field is set
            if instance.club:
                messages.success(request, f"Successfully reviewed {instance.club}!")
            else:
                messages.success(request, f"Successfully reviewed {instance.course}!")

            return redirect(redirect_url)
        return render(
            request,
            "reviews/new_review.html",
            {"form": form, "is_club": is_club, "mode": mode},
        )

    # Prepare context data for GET requests
    context = {"is_club": is_club, "mode": mode}

    # For club reviews, fetch club categories and clubs if needed
    if is_club:
        # Get all club categories for the form
        context["club_categories"] = ClubCategory.objects.all().order_by("name")

        # If a specific club is pre-selected in the URL
        club_id = request.GET.get("club")
        if club_id:
            try:
                club = Club.objects.get(id=club_id)
                context["selected_club"] = club
                context["selected_category"] = club.category
            except Club.DoesNotExist:
                pass

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
            # Check if it's a club or course review
            if form.instance.club:
                messages.success(
                    request,
                    f"Successfully updated your review for {form.instance.club}!",
                )
            else:
                messages.success(
                    request,
                    f"Successfully updated your review for {form.instance.course}!",
                )
            return redirect("reviews")
        messages.error(request, form.errors)
        return render(request, "reviews/edit_review.html", {"form": form})
    form = ReviewForm(instance=review)
    return render(request, "reviews/edit_review.html", {"form": form})


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ["text"]

@login_required
def new_reply(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.review = review
            reply.user = request.user
            try:
                reply.save()
                messages.success(request, "Reply posted.")
            except IntegrityError:
                messages.error(request, "You have already replied to this review.")
    else:
        form = ReplyForm()

    return redirect(f"/course/{review.course.id}/{review.instructor.id}")


@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(Reply, pk=reply_id)
    if reply.user != request.user:
        raise PermissionDenied("You are not allowed to delete this reply!")

    review = reply.review
    reply.delete()
    messages.success(request, "Reply deleted.")
    return redirect(f"/course/{review.course.id}/{review.instructor.id}")

@login_required
def upvote_reply(request, reply_id):
    """Upvote a view."""
    if request.method == "POST":
        reply = Reply.objects.get(pk=reply_id)
        reply.upvote(request.user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})


@login_required
def downvote_reply(request, reply_id):
    """Downvote a view."""
    if request.method == "POST":
        reply = Reply.objects.get(pk=reply_id)
        reply.downvote(request.user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})
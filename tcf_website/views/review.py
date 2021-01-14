"""View pertaining to review creation/viewing."""

from django import forms
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from ..models import Review

# pylint: disable=fixme
# Disable pylint errors on TODO messages, such as below

# TODO: use a proper django form, make it more robust.
# (i.e. better Course/Instructor/Semester search).


class ReviewForm(forms.ModelForm):
    """Form for review creation in the backend, not for rendering HTML."""
    class Meta:
        model = Review
        fields = [
            'text', 'course', 'instructor', 'semester', 'instructor_rating',
            'difficulty', 'recommendability', 'enjoyability', 'amount_reading',
            'amount_writing', 'amount_group', 'amount_homework',
        ]


@login_required
def upvote(request, review_id):
    """Upvote a view."""
    if request.method == 'POST':
        review = Review.objects.get(pk=review_id)
        review.upvote(request.user)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False})


@login_required
def downvote(request, review_id):
    """Downvote a view."""
    if request.method == 'POST':
        review = Review.objects.get(pk=review_id)
        review.downvote(request.user)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False})


@login_required
def new_review(request):
    """Review creation view."""

    # Collect form data into Review model instance.
    if request.method == 'POST':
        # TODO: use a proper django form.
        form = ReviewForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.hours_per_week = \
                instance.amount_reading + instance.amount_writing + \
                instance.amount_group + instance.amount_homework
            instance.save()

            messages.add_message(request, messages.SUCCESS,
                                 f'Successfully reviewed {instance.course}!')
            return redirect('reviews')
        return render(request, 'reviews/new_review.html', {'form': form})
    return render(request, 'reviews/new_review.html')


# Note: Class-based views can't use the @login_required decorator
class DeleteReview(LoginRequiredMixin, generic.DeleteView):
    """Review deletion view."""
    model = Review
    success_url = reverse_lazy('reviews')

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate review belonging to user."""
        obj = super().get_object()
        # For security: Make sure target review belongs to the current user
        if obj.user != self.request.user:
            raise PermissionDenied(
                "You are not allowed to delete this review!")
        return obj

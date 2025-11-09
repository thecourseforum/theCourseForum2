"""Views for user profile."""

from django import forms
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from ..models import Review, User
from .browse import safe_round


class ProfileForm(ModelForm):
    """Form updating user profile."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "graduation_year"]

        # Add the form-control class to make the form work with Bootstrap
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "graduation_year": forms.NumberInput(attrs={"class": "form-control"}),
        }


@login_required
def profile(request):
    """User profile."""
    if not request.user.is_authenticated:
        from django.contrib.auth import login

        # # local dev
        # user, created = User.objects.get_or_create(
        #     username="testuser",
        #     defaults={
        #         "email": "test@test.com",
        #         "first_name": "Test",
        #         "last_name": "User",
        #         "graduation_year": 2025,
        #     },
        # )
        # if created:
        #     user.set_password("testpass123")
        #     user.save()
        # login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        # return HttpResponseRedirect("/profile/")
        # #
    if request.method == "POST":
        form = ProfileForm(request.POST, label_suffix="", instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated successfully!")
        else:
            messages.error(request, form.errors)
        return HttpResponseRedirect("/profile")

    form = ProfileForm(label_suffix="", instance=request.user)

    """User reviews."""
    # Handled separately because it requires joining 1 more table (i.e. Vote)
    upvote_stat = Review.objects.filter(user=request.user).aggregate(
        total_review_upvotes=Count("vote", filter=Q(vote__value=1)),
    )
    # Get other statistics
    other_stats = User.objects.filter(
        id=request.user.id
    ).aggregate(  # karma probably goes in other stats because it's a number like these
        total_reviews_written=Count("review"),
        average_review_rating=(
            Avg("review__instructor_rating")
            + Avg("review__enjoyability")
            + Avg("review__recommendability")
        )
        / 3,
        karma_stat=Count("review", filter=Q(review__vote__value=1))
        - Count("review", filter=Q(review__vote__value=-1)),
    )
    # Merge the two dictionaries
    merged = upvote_stat | other_stats
    # Round floats
    stats = {key: safe_round(value) for key, value in merged.items()}
    # Combine everything into one context
    context = {
        "form": form,
        **stats,  # expands the stats dictionary into the same level
    }
    return render(request, "profile/profile.html", context)


class DeleteProfile(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """User deletion view."""

    model = User
    success_url = reverse_lazy("browse")

    def form_valid(self, form):
        """Override DeleteView's function to just call logout before deleting"""
        # form_valid() is overrideen instead of delete() since it's more in line
        # with what Django expects
        logout(self.request)
        return super().form_valid(form)

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate profile belonging to user."""
        obj = super().get_object()
        # For security: Make sure target review belongs to the current user
        if obj != self.request.user:
            raise PermissionDenied("You are not allowed to delete this account!")
        return obj

    def get_success_message(self, cleaned_data) -> str:
        """Overrides SuccessMessageMixin's get_success_message method."""
        return "Successfully deleted your account!"
        return "Successfully deleted your account!"
        return "Successfully deleted your account!"
        return "Successfully deleted your account!"
        return "Successfully deleted your account!"
        return "Successfully deleted your account!"

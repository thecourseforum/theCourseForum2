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
from .utils import safe_next_url


def _review_stats_for_user(user):
    """Build review stats for a given user."""
    upvote_stat = Review.objects.filter(user=user).aggregate(
        total_review_upvotes=Count("vote", filter=Q(vote__value=1)),
    )
    other_stats = User.objects.filter(id=user.id).aggregate(
        total_reviews_written=Count("review"),
        average_review_rating=(
            Avg("review__instructor_rating")
            + Avg("review__enjoyability")
            + Avg("review__recommendability")
        )
        / 3,
    )
    merged = upvote_stat | other_stats
    return {key: safe_round(value) for key, value in merged.items()}


class ProfileForm(ModelForm):
    """Form for profile page."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "graduation_year"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-group__input"}),
            "last_name": forms.TextInput(attrs={"class": "form-group__input"}),
            "graduation_year": forms.NumberInput(attrs={"class": "form-group__input"}),
        }


@login_required
def profile(request):
    """User profile view."""
    if request.method == "POST":
        form = ProfileForm(request.POST, label_suffix="", instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated successfully!")
        else:
            messages.error(request, form.errors)
        return HttpResponseRedirect("/profile")

    form = ProfileForm(label_suffix="", instance=request.user)
    return render(request, "site/pages/profile.html", {"form": form})


@login_required
def reviews(request):
    """User reviews view."""
    page_number = request.GET.get("page", 1)
    paginated_reviews = Review.paginate(request.user.reviews(), page_number)

    context = _review_stats_for_user(request.user)
    context["paginated_reviews"] = paginated_reviews
    return render(request, "site/pages/reviews.html", context=context)


class DeleteProfile(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """User deletion view."""

    model = User
    success_url = reverse_lazy("browse")

    def get_success_url(self):
        """Use caller-provided next URL when safe, otherwise pick default."""
        return safe_next_url(self.request, str(self.success_url))

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

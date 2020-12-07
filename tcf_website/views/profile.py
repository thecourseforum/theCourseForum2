"""Views for user profile."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django import forms
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from .browse import safe_round
from ..models import Review, User


class ProfileForm(ModelForm):
    """Form updating user profile."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'graduation_year']

        # Add the form-control class to make the form work with Bootstrap
        widgets = {
            'first_name': forms.TextInput(
                attrs={
                    'class': 'form-control'}),
            'last_name': forms.TextInput(
                attrs={
                    'class': 'form-control'}),
            'graduation_year': forms.NumberInput(
                attrs={
                    'class': 'form-control'})}


@login_required
def profile(request):
    """User profile view."""
    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            label_suffix='',
            instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was updated successfully!')
        else:
            messages.error(request, form.errors)
        return HttpResponseRedirect('/profile')

    form = ProfileForm(label_suffix='', instance=request.user)
    return render(request, 'profile/profile.html', {'form': form})


@login_required
def reviews(request):
    """User reviews view."""
    # Handled separately because it requires joining 1 more table (i.e. Vote)
    upvote_stat = Review.objects.filter(user=request.user).aggregate(
        total_review_upvotes=Count('vote', filter=Q(vote__value=1)),
    )
    # Get other statistics
    other_stats = User.objects.filter(id=request.user.id).aggregate(
        total_reviews_written=Count('review'),
        average_review_rating=(
            Avg('review__instructor_rating') +
            Avg('review__enjoyability') +
            Avg('review__recommendability')
        ) / 3,
    )
    # Merge the two dictionaries (NOTE: can be simplified in Python 3.9)
    merged = {**upvote_stat, **other_stats}
    # Round floats
    stats = {key: safe_round(value) for key, value in merged.items()}
    return render(request, 'reviews/user_reviews.html', context=stats)

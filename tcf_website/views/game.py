"""Views for gamification features (game, leaderboard)"""

import datetime

from django import forms
from django.core.cache import cache
from django.core.validators import MaxValueValidator
from django.shortcuts import render

from ..models import Club, Course, Instructor, Review, Semester


class GameForm(forms.Form):
    # fields to be submitted during a guess
    dept = forms.CharField(max_length=4)
    course_number = (
        forms.IntegerField()
    )  # got rid of max_digits=4... was messing up view
    rating = forms.DecimalField(
        max_digits=3, decimal_places=2, validators=[MaxValueValidator(5)]
    )
    difficulty = forms.DecimalField(
        max_digits=3, decimal_places=2, validators=[MaxValueValidator(5)]
    )


cache_timeout = 60 * 60 * 24  # 24 hours


def get_daily_review():  # fetch or retrieve cached daily review, refreshes at midnight
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    cache_key = f"daily_review_{date}"  # cache key has current date

    review = cache.get(cache_key)
    if not review:
        # if the date has changed (12:00 am) then get the new review and reset cache timer
        review = Review.objects.order_by("?").first()
        cache.set(cache_key, review, cache_timeout)

    return review


def game(request):
    if request.method == "GET":
        # fetch random review - check doc for details
        review = get_daily_review()
        return render(request, "game/game.html", {"review": review})

    elif request.method == "POST":
        # process guess
        # use ajax to get feedback information (correctness of guesses) to display on page
        return render(request, "game/game.html")

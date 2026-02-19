"""Views for gamification features (game, leaderboard)"""

import datetime

from django import forms
from django.core.cache import cache
from django.core.validators import MaxValueValidator
from django.shortcuts import render

from ..models import Club, Course, Instructor, Review, Semester


class GameForm(forms.Form):
    #     # fields to be submitted during a guess
    #     dept = forms.CharField(max_length=4)
    #     course_number = (
    #         forms.IntegerField()
    #     )  # got rid of max_digits=4... was messing up view
    #     rating = forms.DecimalField(
    #         max_digit
    # s=3, decimal_places=2, validators=[MaxValueValidator(5)]
    #     )
    #     difficulty = forms.DecimalField(
    #         max_digits=3, decimal_places=2, validators=[MaxValueValidator(5)]
    #     )

    course = forms.CharField(max_length=255, label="Course")
    # commented out because we are not guessing difficulty/other fields


cache_timeout = 60 * 60 * 24  # 24 hours


def get_daily_review():  # fetch or retrieve cached daily review, refreshes at midnight
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    cache_key = f"daily_review_{date}"  # cache key has current date

    review = cache.get(cache_key)
    if not review:
        # if the date has changed (12:00 am) then get the new review and reset cache timer
        review = (
            Review.objects.filter(text__gt="").order_by("?").first()
        )  # reviews w text only
        cache.set(cache_key, review, cache_timeout)

    return review


def print_guess_info(course_text, course_obj=None):
    if course_obj is not None:
        print(f"Guess info - Course: {course_text} (id={course_obj.id})")
    else:
        print(f"Guess info - Course: {course_text} (not valid course")


def game(request):
    courses = Course.objects.all().order_by("subdepartment__mnemonic", "number")

    if request.method == "GET":
        review = get_daily_review()
        form = GameForm()
        return render(
            request,
            "game/game.html",
            {"review": review, "form": form, "courses": courses},
        )

    elif request.method == "POST":
        review = get_daily_review()
        form = GameForm(request.POST)
        info = None
        if form.is_valid():
            course_text = form.cleaned_data["course"]
            # optionally look up Course object
            try:
                course_obj = Course.objects.get(combined_mnemonic_number=course_text)
            except Course.DoesNotExist:
                course_obj = None
            info = print_guess_info(course_text, course_obj)

        # process guess
        # use ajax to get feedback information (correctness of guesses) to display on page
        return render(
            request,
            "game/game.html",
            {"review": review, "form": form, "courses": courses, "info": info},
        )

"""Views for gamification features (game, leaderboard)"""

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


def game(request):
    if request.method == "GET":
        # fetch random review - check doc for details

        review = cache.get("daily_review")
        if not review:
            review = Review.objects.order_by("?").first()
            cache.set("daily_review", review)

        return render(request, "game/game.html", {"review": review})
    elif request.method == "POST":
        # process guess
        # use ajax to get feedback information (correctness of guesses) to display on page
        return render(request, "game/game.html")

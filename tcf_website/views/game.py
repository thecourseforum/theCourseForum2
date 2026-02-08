"""Views for gamification features (game, leaderboard)"""

from django import forms
from django.core.validators import MaxValueValidator
from django.shortcuts import render


class GameForm(forms.Form):
    # fields to be submitted during a guess
    dept = forms.CharField(max_length=4)
    course_number = forms.IntegerField(max_digits=4)
    rating = forms.DecimalField(
        max_digits=3, decimal_places=2, validators=[MaxValueValidator(5)]
    )
    difficulty = forms.DecimalField(
        max_digits=3, decimal_places=2, validators=[MaxValueValidator(5)]
    )


def game(request):
    if request.method == "GET":
        # fetch review - check doc for details
        return render(request, "game.html")
    elif request.method == "POST":
        # process guess
        # use ajax to get feedback information (correctness of guesses) to display on page
        return render(request, "game.html")

"""Views for gamification features (game, leaderboard)"""

import datetime

from django import forms
from django.core.cache import cache
from django.core.validators import MaxValueValidator
from django.shortcuts import render
from django.http import JsonResponse

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


cache_timeout = 60 * 60 * 24  # 24 hours

'''Fetches/retrieves cached daily review, refreshes at midnight'''
def get_daily_review(): 
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    cache_key = f"daily_review_{date}"  # cache key has current date
    review = cache.get(cache_key)
    if not review:
        # if the date has changed (12:00 am) then get the new review and reset cache timer
        review = (
            Review.objects.filter(text__gt="").order_by("?").first() #change later for performance
        )  # reviews w text only
        cache.set(cache_key, review, cache_timeout)

    return review


# def print_guess_info(dept, number, rating, difficulty, gpa):
#     parts = []
#     if dept is not None and number is not None:
#         parts.append(f"{dept} {number}")
#     else:
#         parts.append("unknown course")

#     # other course stats
#     parts.append(f"rating={rating if rating is not None else 'N/A'}")
#     parts.append(f"difficulty={difficulty if difficulty is not None else 'N/A'}")
#     parts.append(f"gpa={gpa if gpa is not None else 'N/A'}")
#     msg = "Guess info - " + ", ".join(parts)

#     print(msg)
#     return msg

'''Extract stats of correct review'''
def get_course_info(course_obj):
    course_id = course_obj.combined_mnemonic_number.split()
    return {
        "dept": course_id[0],
        "number": course_id[1],
        "rating": course_obj.average_rating(),
        "difficulty": course_obj.average_difficulty(),
        "gpa": course_obj.average_gpa(),
    }

'''Returns dict with correct/incorrect or directional hints for numeric fields'''
def compare_guess(review_info, guess_info):
    if guess_info is None:
        return None
    
    feedback = {}

    feedback["dept"] = "correct" if guess_info["dept"] == review_info["dept"] else "incorrect"
    for field in ["number", "rating", "difficulty", "gpa"]:
        g = guess_info[field]
        r = review_info[field]
        if g is None or r is None:  
            feedback[field] = "unknown" 
        elif g == r:
            feedback[field] = "correct"
        elif g < r:
            feedback[field] = "higher" #as in guess needs to be higher
        else:
            feedback[field] = "lower"
    
    return feedback

'''Handles HTTPRequests for game'''
def game(request):
    courses = Course.objects.all().order_by("subdepartment__mnemonic", "number")
    review = get_daily_review()

    if request.method == "GET":
        form = GameForm()
        return render(
            request,
            "game/game.html",
            {"review": review, "form": form, "courses": courses},
        )

    elif request.method == "POST":
        form = GameForm(request.POST)
        feedback = None
        guess_info = None
        review_info = None

        if form.is_valid():
            course_text = form.cleaned_data["course"].upper().split()
            course_mnemonic = course_text[0]
            course_number = course_text[1]
            guess_rating = request.POST.get("rating")
            guess_difficulty = request.POST.get("difficulty")
            guess_gpa = request.POST.get("gpa")

            # looking up course information
            try:
                #guess_course = Course.objects.get(combined_mnemonic_number=course_text)
                #guess_info = get_course_info(guess_course)
                guess_info = {
                    "dept": course_mnemonic,
                    "number": course_number,
                    "rating": float(request.POST.get("rating")) if request.POST.get("rating") else None,
                    "difficulty": float(request.POST.get("difficulty")) if request.POST.get("difficulty") else None,
                    "gpa": float(request.POST.get("gpa")) if request.POST.get("gpa") else None,
                }
                review_info = get_course_info(review.course) 

            except Course.DoesNotExist:
                guess_info = None

            feedback = compare_guess(review_info, guess_info)

        return JsonResponse({
            "feedback": feedback,
            "guess": guess_info,
            "review_info": review_info #for testing 
        })

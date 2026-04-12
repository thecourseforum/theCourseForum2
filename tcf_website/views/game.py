"""Views for gamification features (game, leaderboard)"""

import datetime

from django import forms
from django.core.cache import cache
from django.core.validators import MaxValueValidator
from django.http import JsonResponse
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


cache_timeout = 60 * 60 * 24  # 24 hours

"""Fetches/retrieves cached daily review, refreshes at midnight"""


def get_daily_review():
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    cache_key = f"daily_review_{date}"  # cache key has current date
    review = cache.get(cache_key)
    if not review:
        # if the date has changed (12:00 am) then get the new review and reset cache timer
        review = (
            Review.objects.filter(text__gt="").order_by("?").first()
        )  # reviews w text only, change later for performance
        cache.set(cache_key, review, cache_timeout)
    review = Review.objects.filter(text__gt="").order_by("?").first()
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

"""Extract stats of correct review"""


def safe_round(value, digits=2):
    return round(value, digits) if value is not None else None


def get_course_info(course):
    return {
        "title": course.title,
        "mnemonic": course.subdepartment.mnemonic,
        "number": course.number,
        "school": course.subdepartment.department.school_id,
        "rating": safe_round(course.average_rating(), 2),
        "difficulty": safe_round(course.average_difficulty(), 2),
        "gpa": safe_round(course.average_gpa(), 2),
    }


def _normalize_course_input(course_text: str) -> str:
    return course_text.strip().upper()


def _extract_course_code(course_text: str) -> str:
    """Return the course code portion from inputs like 'CS 1110 — Intro'."""
    return course_text.split("—", 1)[0].strip()


"""Returns dict with correct/incorrect or directional hints for numeric fields"""


def compare_guess(review_info, guess_info):
    if guess_info is None:
        return None

    feedback = {}

    if guess_info.get("mnemonic") == review_info.get("mnemonic"):
        feedback["mnemonic"] = "correct"
    elif guess_info.get("school") and review_info.get("school"):
        feedback["mnemonic"] = (
            "partial"
            if guess_info["school"] == review_info["school"]
            else "incorrect"
        )
    else:
        feedback["mnemonic"] = "incorrect"
    for field in ["number", "rating", "difficulty", "gpa"]:
        g = guess_info[field] if guess_info[field] == None else float(guess_info[field])
        r = (
            review_info[field]
            if review_info[field] == None
            else float(review_info[field])
        )
        if g is None or r is None:
            feedback[field] = "N/A"
        elif g == r:
            feedback[field] = "correct"
        elif g < r:
            feedback[field] = "higher"  # as in guess needs to be higher
        else:
            feedback[field] = "lower"

    return feedback


"""Handles HTTPRequests for game"""


def game(request):
    courses = Course.objects.all().order_by("subdepartment__mnemonic", "number")
    # review = get_daily_review()

    if request.method == "GET":
        # for testing - can get new review per session (cookies cleared)
        review = Review.objects.filter(text__gt="").order_by("?").first()
        request.session["review_id"] = review.id
        form = GameForm()
        return render(
            request,
            "game/game.html",
            {"review": review, "form": form, "courses": courses},
        )

    elif request.method == "POST":
        review = Review.objects.get(id=request.session["review_id"])
        form = GameForm(request.POST)
        feedback = None
        guess_info = None
        review_info = None

        if form.is_valid():
            raw_course_text = form.cleaned_data["course"]
            course_text = _normalize_course_input(raw_course_text)
            course_code = _extract_course_code(course_text)

            # looking up course information
            try:
                if course_code:
                    guess_course = Course.objects.get(
                        combined_mnemonic_number=course_code
                    )
                else:
                    raise Course.DoesNotExist
                guess_info = get_course_info(guess_course)
                review_info = get_course_info(review.course)

            except Course.DoesNotExist:
                guess_course = Course.objects.filter(
                    title__icontains=course_text
                ).first()
                if guess_course:
                    guess_info = get_course_info(guess_course)
                    review_info = get_course_info(review.course)
                else:
                    guess_info = None

            feedback = compare_guess(review_info, guess_info)

        return JsonResponse(
            {
                "feedback": feedback,
                "guess": guess_info,
                "review_info": review_info,  # for testing
            }
        )

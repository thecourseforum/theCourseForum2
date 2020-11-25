# pylint: disable=fixme,broad-except
"""View pertaining to review creation/viewing."""

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect

from ..models import Review, Course, Semester, Instructor

# TODO: use a proper django form, make it more robust.
# (i.e. better Course/Instructor/Semester search).


class ReviewForm(forms.Form):
    """Form for review creation."""


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
            try:
                course_id = request.POST['course']
                course = Course.objects.get(id=int(course_id))

                instructor_id = request.POST['instructor']
                instructor = Instructor.objects.get(id=int(instructor_id))

                semester_id = request.POST['semester']
                semester = Semester.objects.get(id=int(semester_id))

                hours_reading = int(request.POST['hoursReading'])
                hours_writing = int(request.POST['hoursWriting'])
                hours_group = int(request.POST['hoursGroupwork'])
                hours_other = int(request.POST['hoursOther'])
                total_hours = hours_reading + hours_writing + hours_group + hours_other

                Review.objects.create(
                    user=request.user,
                    course=course,
                    semester=semester,
                    instructor=instructor,
                    text=request.POST['reviewText'],
                    instructor_rating=int(request.POST['instructorRating']),
                    enjoyability=int(request.POST['enjoyability']),
                    difficulty=int(request.POST['difficulty']),
                    recommendability=int(request.POST['recommendability']),
                    amount_reading=hours_reading,
                    amount_writing=hours_writing,
                    amount_group=hours_group,
                    amount_homework=hours_other,
                    hours_per_week=total_hours
                )

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Successfully reviewed ' +
                    str(course) + '!')
                return redirect('reviews')
            except BaseException:  # TODO: need more robust backend validation
                print("Review error")
                messages.add_message(
                    request,
                    messages.ERROR,
                    'This course is invalid. Try again!')
                return render(request, 'reviews/new_review.html', {'form': form})
        else:
            return render(request, 'reviews/new_review.html', {'form': form})

    form = ReviewForm()
    return render(request, 'reviews/new_review.html', {'form': form})

from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login
from django.http import JsonResponse
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django import forms

from ..models import Review, Course, Semester, Instructor

# TODO: use a proper django form, make it more robust (i.e. better Course/Instructor/Semester search).
class ReviewForm(forms.Form):
    pass

@login_required
def new_review(request):
    if request.method == 'POST':
        # TODO: use a proper django form.
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                course_code = request.POST['course']
                mnemonic, number = course_code.split()
                course = Course.objects.get(subdepartment__mnemonic=mnemonic, number=int(number))

                instructor_name = request.POST['instructor']
                first, last = instructor_name.split()
                instructor = Instructor.objects.get(first_name=first, last_name=last)

                semester_str = request.POST['semester']
                season, year = semester_str.split()
                semester = Semester.objects.get(season=season.upper(), year=int(year))

                instructor_rating = int(request.POST['instructorRating'])
                difficulty = int(request.POST['difficulty'])
                recommendability = int(request.POST['recommendability'])
                hours = int(request.POST['hours'])
                text = request.POST['reviewText']

                Review.objects.create(
                    user=request.user,
                    course=course,
                    semester=semester,
                    instructor=instructor,
                    text=text,
                    instructor_rating=instructor_rating,
                    difficulty=difficulty,
                    recommendability=recommendability,
                    hours_per_week=hours,
                )

                return redirect('reviews')
            except Exception as e:
                print(e)
                print(request.POST)
                return render(request, 'reviews/new.html', {'form': form})
        else:
            print("error")
            print(form)
            return render(request, 'reviews/new.html', {'form': form})
    
    form = ReviewForm()
    return render(request, 'reviews/new.html', {'form': form})
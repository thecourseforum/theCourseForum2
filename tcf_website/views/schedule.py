"""View pertaining to schedule creation/viewing."""

# from django import forms
# from django.views import generic
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
# from django.contrib.messages.views import SuccessMessageMixin
# from django.core.exceptions import PermissionDenied
# from django.contrib import messages
# from django.http import JsonResponse
# from django.shortcuts import get_object_or_404, render, redirect
from django.shortcuts import render
# from django.urls import reverse_lazy

# from ..models import Schedule


@login_required
def view_schedules(request):
    '''
    get all schedules for a given user
    '''
    if request.method == 'GET':
        # form = ReviewForm(request.POST)
        # if form.is_valid():
        #     instance = form.save(commit=False)
        #     instance.user = request.user
        #     instance.hours_per_week = \
        #         instance.amount_reading + instance.amount_writing + \
        #         instance.amount_group + instance.amount_homework

        #     instance.save()

        #     messages.success(request,
        #                      f'Successfully reviewed {instance.course}!')
        #     return redirect('reviews')
        # return render(request, 'reviews/new_review.html', {'form': form})

        pass
    return render(request, 'schedule/user_schedules.html')

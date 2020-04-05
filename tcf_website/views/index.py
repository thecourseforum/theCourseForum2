from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login
from django.http import JsonResponse
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder

from ..models import School, Department

def index(request):
    if request.user.is_authenticated:
        return redirect('browse')
    return render(request, 'landing/landing.html')    


def about(request):
    return render(request, 'about/about.html')    
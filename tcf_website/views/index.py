"""Views for index and about pages."""
from django.shortcuts import render, redirect


def index(request):
    """Index view."""
    if request.user.is_authenticated:
        return redirect('browse')
    return render(request, 'landing/landing.html')


def about(request):
    """About view."""
    return render(request, 'about/about.html')


def privacy(request):
    """Privacy view."""
    return render(request, 'about/privacy.html')


def terms(request):
    """Terms view."""
    return render(request, 'about/terms.html')

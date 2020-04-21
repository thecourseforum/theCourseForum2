"""Views for search results"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def search(request):
    """Search results view."""
    return render(request, 'search/search.html')

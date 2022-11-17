"""View for ads.txt."""
from django.http import HttpResponse


# pylint: disable=unused-argument
def ads(request):
    """
    Serves the following line when thecourseforum.com/ads.txt is accessed,
    as part of the authorized digital sellers specification.
    https://iabtechlab.com/ads-txt/
    """
    line = 'google.com, pub-1816162577232603, DIRECT, f08c47fec0942fa0'
    return HttpResponse(line)

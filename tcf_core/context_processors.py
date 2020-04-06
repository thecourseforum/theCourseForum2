from django.conf import settings

from tcf_website.models import Semester

def base(request):
    return {'DEBUG': settings.DEBUG, 'USER': request.user, 'LATEST_SEMESTER': Semester.latest()}
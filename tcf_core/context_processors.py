from django.conf import settings

def base(request):
    return {'DEBUG': settings.DEBUG, 'USER': request.user}
"""Posting to Feedback"""
import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail


@require_http_methods('POST')
def send_discord(query):
    """Post message to discord server"""
    message_type = query.POST.get("type", "bug")
    url = os.environ['DISCORD_URL_BUG']
    if message_type == "feedback":
        url = os.environ['DISCORD_URL_FEEDBACK']

    content = {'content': query.POST.get("content", "")}
    json_data = json.dumps(content)
    requests.post(
        url, data=json_data, headers={
            "Content-Type": "application/json"})
    return return JsonResponse({'ok': True, 'content': content})


@require_http_methods('POST')
def send_email(query):
    """Send email to support"""
    subject = query.POST.get("subject", "")
    content = query.POST.get("content", "")
    from_email = os.environ['EMAIL_HOST_USER']
    to_email = query.POST.get("recipients", from_email)
    recipient_list = [
        to_email,
        from_email
    ]

    if subject and content and from_email and recipient_list:
        try:
            send_mail(subject, content, from_email, recipient_list)
        except BadHeaderError:
            return JsonResponse({'ok': False, 'content': content})
        return JsonResponse({'ok': True, 'content': content})
    else:
        return JsonResponse({'ok': False, 'content': content})

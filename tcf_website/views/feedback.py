"""Sending Feedback"""
import os
import json
import requests
from django.http import JsonResponse
from django.core.mail import send_mail

def send_discord(query):
    """Post message to discord server"""
    message_type = query.GET.get("type", "bug")
    url = os.environ['DISCORD_URL_BUG']
    if message_type == "feedback":
        url = os.environ['DISCORD_URL_FEEDBACK']

    content = {'content': query.GET.get("content", "")}
    json_data = json.dumps(content)
    requests.post(
        url, data=json_data, headers={
            "Content-Type": "application/json"})
    return JsonResponse(content)

def send_email(query):
    """Send email to support"""
    subject = query.GET.get("subject", "")
    content = query.GET.get("content", "")
    from_email = os.environ['EMAIL_HOST_USER']
    recipient_list = ["support@thecourseforum.com"]

    send_mail(subject, content, from_email, recipient_list)
    return JsonResponse({'content': query.GET.get("content", "")})

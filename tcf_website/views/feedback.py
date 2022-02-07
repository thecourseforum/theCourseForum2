"""Posting to Feedback"""
import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import BadHeaderError, send_mail


def send_discord(url, message):
    """Post message to discord server"""
    json_data = json.dumps(message)
    requests.post(
        url, data=json_data, headers={
            "Content-Type": "application/json"})
    return JsonResponse({'ok': True, 'content': message})


def send_email(subject, message, from_email, recipient_list):
    """Send email"""
    try:
        send_mail(subject, message, from_email, recipient_list)
    except BadHeaderError:
        return JsonResponse({'ok': False, 'content': message})
    return JsonResponse({'ok': True, 'content': message})


@require_http_methods('POST')
def discord_feedback(query):
    """Prepare feedback for discord message"""
    message_type = query.POST.get("type", "")
    content = query.POST.get("content", {})

    if message_type == "bug":
        url = os.environ['DISCORD_URL_BUG']
        message = f"""Bug Found!
                    **URL:** {content.url}
                    **Categories:** {content.categories}
                    **Email:** {content.email}
                    **Description:** {content.description}""".format(content)
        return send_discord(url, message)
    if message_type == "feedback":
        url = os.environ['DISCORD_URL_FEEDBACK']
        message = f"""Feedback submitted
                    **Name:** {content.fname} {content.lname}
                    **Email:** {content.email}
                    **Title:** {content.title}
                    **Message:** {content.message}""".format(content)
        return send_discord(url, message)
    return JsonResponse({'ok': False, 'content': query})


@require_http_methods('POST')
def email_feedback(query):
    """Prepare feedback for email"""
    message_type = query.POST.get("type", "")
    content = query.POST.get("content", "")
    from_email = os.environ['EMAIL_HOST_USER']
    to_email = content["email"]
    recipient_list = [
        to_email,
        from_email
    ]
    subject = "[theCourseForum] Thank you for your feedback!"

    if message_type == "bug":
        message = f"""Thanks for reaching out! We received the following bug report from you:
                    Description: {content.description}
                    Categories: {content.categories}
                    We apologize for any inconveniences that this may have caused.
                    Our team will be investigating the issue and will follow up with you shortly.
                    Best,
                    theCourseForum Team""".format(content)
        return send_email(subject, message, from_email, recipient_list)
    if message_type == "feedback":
        message = f"""Hi {content.fname},
                    Thanks for reaching out! We received the following feedback from you:
                    Title: {content.title}
                    Message: {content.message}
                    We greatly appreciate you taking the time to help us improve tCF!
                    A team member will be following up with you shortly if neccesary.
                    Best,
                    theCourseForum Team""".format(content)
        return send_email(subject, message, from_email, recipient_list)
    return JsonResponse({'ok': False, 'content': query})

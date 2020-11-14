"""Posting to Discord"""
import os
import json
import requests
from django.http import JsonResponse


def post_message(query):
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

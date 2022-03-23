"""Posting to Discord"""
import os
import json
import requests
import requests_toolbelt.adapters.appengine
from django.http import JsonResponse

# Needed for requests to work on GAE
requests_toolbelt.adapters.appengine.monkeypatch()

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

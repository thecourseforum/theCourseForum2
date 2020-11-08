"""Posting to Discord"""
import os
import json
import requests
from django.http import JsonResponse


def post_bug(query):
    """Post message to discord server"""
    url = os.environ['DISCORD_URL_BUG']
    content = {'content': query.GET.get('content', '')}
    json_data = json.dumps(content)
    requests.post( url, data=json_data, headers={"Content-Type": "application/json"})
    return JsonResponse(content)

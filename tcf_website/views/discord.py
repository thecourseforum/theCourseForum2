"""Posting to Discord"""
import os
import json
import requests
from django.http import JsonResponse

def post_bug(query):
    discord_url = os.environ['DISCORD_URL_BUG']
    content = {'content': query.GET.get('content', '')}
    result = requests.post(discord_url, data=json.dumps(content), headers={"Content-Type": "application/json"})
    return JsonResponse(content)

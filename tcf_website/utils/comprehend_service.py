import boto3
from django.conf import settings

class ComprehendService:
    def __init__(self):
        self.client = boto3.client(
            'comprehend',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name='us-east-1'
        )

    def detect_sentiment(self, text, language_code="en"):
        response = self.client.detect_sentiment(Text=text, LanguageCode=language_code)
        return response["Sentiment"]

    def detect_entities(self, text, language_code="en"):
        response = self.client.detect_entities(Text=text, LanguageCode=language_code)
        return response["Entities"]

    def detect_key_phrases(self, text, language_code="en"):
        response = self.client.detect_key_phrases(Text=text, LanguageCode=language_code)
        return response["KeyPhrases"]

    def detect_language(self, text):
        response = self.client.detect_dominant_language(Text=text)
        return response["Languages"]

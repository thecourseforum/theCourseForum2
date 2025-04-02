from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..utils.comprehend_service import ComprehendService
from detoxify import Detoxify


@csrf_exempt
def analyze_text(request):
    if request.method == "POST":
        text = request.POST.get("text", "")
        print(Detoxify("original").predict(text) )
        # comprehend = ComprehendService()
        # sentiment = comprehend.detect_sentiment(text)
        # entities = comprehend.detect_entities(text)
        # key_phrases = comprehend.detect_key_phrases(text)
        return JsonResponse({"hi": "yo"}, status=200)
        # return JsonResponse(
        #     {"sentiment": sentiment, "entities": entities, "key_phrases": key_phrases}
        # )
    return JsonResponse({"error": "Invalid request"}, status=400)

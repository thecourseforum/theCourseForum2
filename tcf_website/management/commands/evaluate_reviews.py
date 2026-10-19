import boto3
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

from tcf_website.models import Review

CHECKPOINT_KEY = "evaluate_reviews:last_run"


class Command(BaseCommand):
    help = "Evaluate new reviews, or all reviews when --all is provided."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Evaluate all reviews instead of only reviews since the last run.",
        )

    def handle(self, *args, **options):
        run_started_at = timezone.now()
        reviews = self._reviews_since_last_run(options["all"])

        for review in reviews:
            self._evaluate_review(review)

        cache.set(CHECKPOINT_KEY, run_started_at.isoformat())
        self.stdout.write(f"Processed {len(reviews)} review(s).")

    def _reviews_since_last_run(self, evaluate_all):
        reviews = Review.objects.exclude(text="").order_by("created", "id")
        if evaluate_all:
            return reviews

        last_run = cache.get(CHECKPOINT_KEY)
        if last_run is None:
            return reviews

        return reviews.filter(created__gt=timezone.datetime.fromisoformat(last_run))

    def _evaluate_review(self, review):
        text = review.text

        if not text or not getattr(settings, "ENABLE_REVIEW_MODERATION", False):
            return None

        client = boto3.client(
            "bedrock-runtime", region_name=getattr(settings, "AWS_REGION", "us-east-1")
        )

        response = client.converse(
            modelId="mistral.voxtral-mini-3b-2507",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": (
                                "Evaluate this review for inappropriate, "
                                "offensive, or harmful content. "
                                "Respond with APPROVED or FLAGGED and "
                                "a brief explanation.\n\n"
                                f"Review: {text}"
                            )
                        }
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 200, "temperature": 0},
        )

        result = response["output"]["message"]["content"][0]["text"]

        self.stdout.write(f"Review {review.id}: {result}")

        return result

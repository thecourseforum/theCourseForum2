from detoxify import Detoxify
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from tcf_website.models import Review

"""
Command for evaluating toxicity of existing reviews
use: docker exec -it tcf_django python manage.py evaluate_review_toxicity
"""


class Command(BaseCommand):

    help = (
        "Assigns toxicity with:"
        "Overall toxicity on a scale of 0-1, "
        "Most relevant category out of obscene, threat, insult, identity_attack or sexual_explicit"
    )

    def add_arguments(self, parser):
        # parser.add_argument("--log", action="store_true", help="Prints out reviews as they are processed")
        parser.add_argument(
            "--results", action="store_true", help="View results of evaluation"
        )

    """Standard Django function implementation - runs when this command is executed."""

    def handle(self, *args, **options):
        if options["results"]:
            self.view_results()
            return

        try:
            model = Detoxify("original")
        except Exception as e:
            raise CommandError(f"Error initializing Detoxify: {e}")

        reviews = Review.objects.all()
        if not reviews:
            self.stdout.write("No reviews found to process.")
            return

        toxicity_categories = [
            "obscene",
            "threat",
            "insult",
            "identity_attack",
            # "sexual_explicit", doesn't exist for original model
        ]

        for review in tqdm(reviews, desc="Processing reviews..", unit="review"):
            if review.text:  # evaluate if there is text + no rating
                try:
                    prediction = model.predict(review.text)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Error processing review {review.id}: {e}")
                    )
                    continue
                review.toxicity_rating = round(100 * prediction["toxicity"])

                # get most relevant toxicity category
                max_label = max(
                    toxicity_categories, key=lambda label: prediction[label]
                )
                review.toxicity_category = max_label
                review.save()
        self.stdout.write(self.style.SUCCESS("Finished evaluating reviews :)"))

    """Used to check for any abnormalities after filtering. Only used for testing, this prints to console"""

    def view_results(self):
        self.stdout.write("Printing out all toxic reviews...")
        removed_reviews = Review.objects.filter(
            toxicity_rating__gte=settings.TOXICITY_THRESHOLD
        ).order_by("toxicity_rating")
        for review in removed_reviews:
            self.stdout.write(str(review.toxicity_rating) + " - " + review.text)
        self.stdout.write(self.style.SUCCESS("Finished retrieving reviews :)"))

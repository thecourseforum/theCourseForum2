from detoxify import Detoxify
from tdqm import tdqm
from django.core.management.base import BaseCommand, CommandError

from tcf_website.models import Review

"""
Command for evaluating toxicity of existing reviews
use: docker exec -it tcf_django python manage.py evaluate_reviews
"""
class Command(BaseCommand):

    help = (
        "Assigns toxicity with:"
        "Overall toxicity on a scale of 0-1, "
        "Most relevant category out of obscene, threat, insult, identity_attack or sexual_explicit"
    )

    def add_arguments(self, parser):
        parser.add_argument("--log", action="store_true", help="Prints out reviews as they are processed")

    """Standard Django function implementation - runs when this command is executed."""
    def handle(self, *args, **options):
        log = options["log"]
        
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
            #"sexual_explicit", doesn't exist for original model
        ]

        for review in tdqm(reviews, desc="Processing reviews..", unit="review"):
            if review.text and review.toxicity_catgory:  # evaluate if there is text + no rating
                try:
                    prediction = model.predict(review.text)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Error processing review {review.id}: {e}")
                    )
                    continue
                review.toxicity_rating = prediction["toxicity"]

                # get most relevant toxicity category
                max_label = max(toxicity_categories, key=lambda label: prediction[label])
                review.toxicity_catgory = max_label
                review.save()
        self.stdout.write(self.style.SUCCESS("Finished evaluating reviews :)"))

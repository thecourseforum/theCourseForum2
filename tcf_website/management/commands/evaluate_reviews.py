from detoxify import Detoxify
from django.core.management.base import BaseCommand, CommandError

from tcf_website.models import Review


class Command(BaseCommand):
    """Command that is run for assigning toxicity ratings to existing reviews"""

    help = (
        "Assigns toxicity ratings to existing reviews of"
        "Overall toxicity on a scale of 1-10, "
        "Most relevant category out of obscene, threat, insult, identity_attack or sexual_explicit"
    )

    def handle(self):
        """Standard Django function implementation - runs when this command is executed."""
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
            "sexual_explicit",
        ]

        for review in reviews:
            if review.text is not "":  # evaluate if there is text
                try:
                    prediction = model.predict(review.text)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Error processing review {review.id}: {e}")
                    )
                    continue
                review.toxicity_rating = prediction.get("toxicity", 0)

                # get most relevant toxicity category
                max_label = max(toxicity_categories, key=lambda label: prediction.get(label, 0))
                # max_score = predictions.get(max_label, 0)
                # print(f"Max label: {max_label}, Max score: {max_score}")
                review.toxicity_catgory = max_label
                review.save()
        self.stdout.write(self.style.SUCCESS("Finished evaluating reviews :)"))

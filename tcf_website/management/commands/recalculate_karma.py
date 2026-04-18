from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from tcf_website.models import User


class Command(BaseCommand):
    help = "Recalculates karma for all users based on their existing data history."

    def handle(self, *args, **options):
        users = User.objects.all()
        self.stdout.write(f"Calculating karma for {users.count()} users...")

        for user in users:
            karma = 0

            # Base contributions
            karma += user.review_set.count() * 10
            karma += user.question_set.count() * 5
            karma += user.answer_set.count() * 10
            karma += user.schedule_set.count() * 2

            # Votes received on Reviews
            review_votes = user.review_set.aggregate(
                upvotes=Count("vote", filter=Q(vote__value=1)),
                downvotes=Count("vote", filter=Q(vote__value=-1)),
            )
            karma += (review_votes["upvotes"] * 10) - (review_votes["downvotes"] * 2)

            # Votes received on Questions
            question_votes = user.question_set.aggregate(
                upvotes=Count("votequestion", filter=Q(votequestion__value=1)),
                downvotes=Count("votequestion", filter=Q(votequestion__value=-1)),
            )
            karma += (question_votes["upvotes"] * 5) - (question_votes["downvotes"] * 2)

            # Votes received on Answers
            answer_votes = user.answer_set.aggregate(
                upvotes=Count("voteanswer", filter=Q(voteanswer__value=1)),
                downvotes=Count("voteanswer", filter=Q(voteanswer__value=-1)),
            )
            karma += (answer_votes["upvotes"] * 10) - (answer_votes["downvotes"] * 2)

            # Ensure karma is within constraints (0 to 5000)
            user.karma = min(5000, max(0, karma))
            user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully recalculated karma for {users.count()} users!"
            )
        )

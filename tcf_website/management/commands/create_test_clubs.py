from django.core.management.base import BaseCommand
import random
from django.utils import timezone
from datetime import timedelta

from tcf_website.models import ClubCategory, Club, User, Review, Semester


class Command(BaseCommand):
    help = "Creates test club categories, clubs, and reviews"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Creating test club data..."))

        # Get the latest semester for reviews
        latest_semester = Semester.latest()
        if not latest_semester:
            self.stdout.write(
                self.style.ERROR(
                    "Error: No semesters found. Please load semester data first."
                )
            )
            return

        # Get a user to associate reviews with
        users = list(User.objects.all())
        if not users:
            self.stdout.write(
                self.style.ERROR(
                    "Error: No users found. Please create at least one user first."
                )
            )
            return

        # Create club categories
        categories = [
            {
                "name": "Academic",
                "slug": "ACAD",
                "description": "Clubs focused on academic pursuits and learning",
            },
            {
                "name": "Cultural",
                "slug": "CULT",
                "description": "Clubs representing various cultures and traditions",
            },
            {
                "name": "Service",
                "slug": "SERV",
                "description": "Community service and volunteer organizations",
            },
            {
                "name": "Sports & Recreation",
                "slug": "SPORT",
                "description": "Athletic and recreational clubs",
            },
            {
                "name": "Arts & Performance",
                "slug": "ARTS",
                "description": "Creative arts, music, and performance groups",
            },
        ]

        category_objects = []
        for cat_data in categories:
            category, created = ClubCategory.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                },
            )
            category_objects.append(category)
            action = "Created" if created else "Found existing"
            self.stdout.write(f"{action} category: {category.name}")

        # Create clubs
        clubs_data = [
            # Academic clubs
            {
                "name": "Computer Science Club",
                "description": "A club for students interested in computer science and programming",
                "category": "ACAD",
            },
            {
                "name": "Math Club",
                "description": "For math enthusiasts to solve problems and discuss mathematical topics",
                "category": "ACAD",
            },
            {
                "name": "Pre-Medical Society",
                "description": "Supports students pursuing careers in medicine and healthcare",
                "category": "ACAD",
            },
            # Cultural clubs
            {
                "name": "Asian Student Union",
                "description": "Celebrates Asian cultures and traditions",
                "category": "CULT",
            },
            {
                "name": "Hispanic Student Association",
                "description": "Promotes Hispanic culture and heritage",
                "category": "CULT",
            },
            # Service clubs
            {
                "name": "Volunteer Corps",
                "description": "Coordinates volunteer opportunities in the community",
                "category": "SERV",
            },
            {
                "name": "Habitat for Humanity Chapter",
                "description": "Works on housing projects for those in need",
                "category": "SERV",
            },
            # Sports clubs
            {
                "name": "Ultimate Frisbee Club",
                "description": "Casual and competitive ultimate frisbee",
                "category": "SPORT",
            },
            {
                "name": "Climbing Club",
                "description": "Rock climbing enthusiasts of all levels",
                "category": "SPORT",
            },
            # Arts clubs
            {
                "name": "Acapella Group",
                "description": "Student-run acapella singing group",
                "category": "ARTS",
            },
            {
                "name": "Photography Club",
                "description": "For students interested in photography techniques and outings",
                "category": "ARTS",
            },
        ]

        club_objects = []
        for club_data in clubs_data:
            category = ClubCategory.objects.get(slug=club_data["category"])
            club, created = Club.objects.get_or_create(
                name=club_data["name"],
                category=category,
                defaults={"description": club_data["description"]},
            )
            club_objects.append(club)
            action = "Created" if created else "Found existing"
            self.stdout.write(f"{action} club: {club.name}")

        # Create reviews
        review_texts = [
            "This club has been a great experience! The leadership is supportive and the events are well organized. I've made great friends and learned a lot.",
            "I joined this club last semester and it's been a mixed experience. The meetings can be disorganized, but the members are friendly.",
            "Highly recommend joining this club! The time commitment is reasonable and the activities are very enjoyable.",
            "This club requires more time than I expected, but it's worth it. The leadership is excellent and I've developed valuable skills.",
            "Decent club overall. The meetings could be more engaging but I appreciate the community service opportunities.",
            "I've been a member for two years and have seen the club improve significantly. Great leadership team and welcoming atmosphere.",
            "Not the best club experience. Meetings often get canceled last minute and communication is poor.",
            "Amazing club! The events are fun and the people are friendly. Reasonable time commitment that works with my schedule.",
            "This club has helped me develop leadership skills and make connections across campus. Highly recommend!",
            "Interesting club concept but the execution is lacking. Meeting times are inconsistent and activities aren't well planned.",
        ]

        reviews_created = 0
        for club in club_objects:
            # Create 2-5 reviews per club
            num_reviews = random.randint(2, 5)
            for _ in range(num_reviews):
                # Random user and review text
                user = random.choice(users)
                text = random.choice(review_texts)

                # Random ratings between 1-5
                instructor_rating = random.randint(1, 5)
                difficulty = random.randint(1, 5)
                recommendability = random.randint(1, 5)
                enjoyability = random.randint(1, 5)

                # Random hours between 0-10 for each category
                amount_reading = random.randint(0, 10)
                amount_writing = random.randint(0, 10)
                amount_group = random.randint(0, 10)
                amount_homework = random.randint(0, 10)
                hours_per_week = (
                    amount_reading + amount_writing + amount_group + amount_homework
                )

                # Random date within last year
                days_ago = random.randint(0, 365)
                created_date = timezone.now() - timedelta(days=days_ago)

                # Find an instructor for the review since it's required
                # The instructor field in Review is required even for club reviews
                try:
                    from tcf_website.models import Instructor

                    instructor = Instructor.objects.order_by("?").first()
                    if not instructor:
                        self.stdout.write(
                            self.style.ERROR(
                                "Error: No instructors found. Please create at least one instructor first."
                            )
                        )
                        return

                    # Find a course for the review since it's required
                    from tcf_website.models import Course

                    course = Course.objects.order_by("?").first()
                    if not course:
                        self.stdout.write(
                            self.style.ERROR(
                                "Error: No courses found. Please create at least one course first."
                            )
                        )
                        return
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
                    return

                review, created = Review.objects.get_or_create(
                    user=user,
                    club=club,
                    semester=latest_semester,
                    defaults={
                        "text": text,
                        "instructor_rating": instructor_rating,
                        "difficulty": difficulty,
                        "recommendability": recommendability,
                        "enjoyability": enjoyability,
                        "amount_reading": amount_reading,
                        "amount_writing": amount_writing,
                        "amount_group": amount_group,
                        "amount_homework": amount_homework,
                        "hours_per_week": hours_per_week,
                        "created": created_date,
                        "modified": created_date,
                        "instructor": instructor,  # Required field
                        "course": course,  # Required field
                    },
                )

                if created:
                    reviews_created += 1
                    self.stdout.write(
                        f"Created review for {club.name} by {user.username}"
                    )
                else:
                    self.stdout.write(
                        f"Found existing review for {club.name} by {user.username}"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Test data creation complete! Created {len(category_objects)} categories, {len(club_objects)} clubs, and {reviews_created} reviews."
            )
        )

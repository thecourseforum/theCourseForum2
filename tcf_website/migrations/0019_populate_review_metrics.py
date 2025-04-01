# In the new migration file
from django.db import migrations


def populate_metrics(apps, schema_editor):
    Review = apps.get_model("tcf_website", "Review")
    CourseInstructorMetrics = apps.get_model("tcf_website", "CourseInstructorMetrics")
    Course = apps.get_model("tcf_website", "Course")

    # Group reviews by course-instructor and calculate metrics
    metrics_data = {}
    course_metrics = {}

    # First, collect all reviews and group them
    for review in Review.objects.all():
        # For course-instructor metrics
        key = (review.course_id, review.instructor_id)
        if key not in metrics_data:
            metrics_data[key] = {
                "course_id": review.course_id,
                "instructor_id": review.instructor_id,
                "reviews": [],
            }
        metrics_data[key]["reviews"].append(review)

        # For course metrics
        if review.course_id not in course_metrics:
            course_metrics[review.course_id] = {"reviews": []}
        course_metrics[review.course_id]["reviews"].append(review)

    # Calculate and save metrics for each course-instructor group
    for data in metrics_data.values():
        reviews = data["reviews"]
        n = len(reviews)

        if n > 0:
            # Calculate average values (using average() method won't work in migration)
            avg_rating = (
                sum(
                    (r.instructor_rating + r.recommendability + r.enjoyability) / 3 for r in reviews
                )
                / n
            )
            avg_difficulty = sum(r.difficulty for r in reviews) / n
            avg_recommendability = sum(r.recommendability for r in reviews) / n
            avg_enjoyability = sum(r.enjoyability for r in reviews) / n
            avg_instructor_rating = sum(r.instructor_rating for r in reviews) / n
            avg_hours_per_week = sum(r.hours_per_week for r in reviews) / n
            avg_amount_reading = sum(r.amount_reading for r in reviews) / n
            avg_amount_writing = sum(r.amount_writing for r in reviews) / n
            avg_amount_group = sum(r.amount_group for r in reviews) / n
            avg_amount_homework = sum(r.amount_homework for r in reviews) / n

            # Create and save metrics
            metrics = CourseInstructorMetrics(
                course_id=data["course_id"],
                instructor_id=data["instructor_id"],
                review_count=n,
                avg_rating=avg_rating,
                avg_difficulty=avg_difficulty,
                avg_recommendability=avg_recommendability,
                avg_enjoyability=avg_enjoyability,
                avg_instructor_rating=avg_instructor_rating,
                avg_hours_per_week=avg_hours_per_week,
                avg_amount_reading=avg_amount_reading,
                avg_amount_writing=avg_amount_writing,
                avg_amount_group=avg_amount_group,
                avg_amount_homework=avg_amount_homework,
            )
            metrics.save()

    # Update course metrics
    for course_id, data in course_metrics.items():
        reviews = data["reviews"]
        n = len(reviews)

        if n > 0:
            avg_rating = (
                sum(
                    (r.instructor_rating + r.recommendability + r.enjoyability) / 3 for r in reviews
                )
                / n
            )
            avg_difficulty = sum(r.difficulty for r in reviews) / n
            avg_hours_per_week = sum(r.hours_per_week for r in reviews) / n

            course = Course.objects.get(pk=course_id)
            course.avg_rating = avg_rating
            course.avg_difficulty = avg_difficulty
            course.avg_hours_per_week = avg_hours_per_week
            course.review_count = n
            course.save()


class Migration(migrations.Migration):

    dependencies = [
        (
            "tcf_website",
            "0018_course_avg_difficulty_course_avg_hours_per_week_and_more",
        ),  # Replace with actual previous migration
    ]

    operations = [
        migrations.RunPython(populate_metrics),
    ]
